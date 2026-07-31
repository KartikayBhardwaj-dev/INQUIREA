from __future__ import annotations

import logging
from typing import Any
from backend.app.models.users import User
from backend.app.services.google_token_service import GoogleTokenService
from sqlalchemy.orm import Session
from backend.app.models.email import Email
from backend.app.models.draft_reply import DraftReply
from backend.app.services.approval_service import ApprovalService
from backend.app.services.draft_service import DraftService
from backend.app.services.gmail_service import GmailService

logger = logging.getLogger(__name__)


class GmailActionService:

    """
    Gmail action orchestration service.

    Handles:
    - Draft validation
    - Approval validation
    - Gmail API execution
    - Database synchronization
    """

    def __init__(
    self,
    db: Session,
):
        self.db = db
        self.approval_service = ApprovalService(db)
        self.draft_service = DraftService(db)

    async def _get_gmail_service(
    self,
    user_id: int,
) -> GmailService:

        user = (
        self.db.query(User)
        .filter(User.id == user_id)
        .first()
    )

        if user is None:
            raise ValueError("User not found.")

        access_token = await GoogleTokenService.refresh_access_token(
        user=user,
        db=self.db,
    )

        return GmailService(access_token)

    def _load_email(
    self,
    email_id: int,
) -> Email:

        email = (
        self.db.query(Email)
        .filter(
            Email.id == email_id
        )
        .first()
    )

        if email is None:
            raise ValueError(
            f"Email {email_id} not found."
        )

        return email
    async def send_reply(
        self,
        draft_id: int,
        user_id: int,
    ) -> dict[str, Any]:

        draft = self._load_draft(
            draft_id,
            user_id=user_id
        )

        self._ensure_approved(draft_id,user_id)

        if not draft.gmail_draft_id:
            raise ValueError(
                f"Draft {draft_id} has no Gmail draft ID. "
                "Save draft to Gmail first."
            )

        gmail = await self._get_gmail_service(user_id)

        send_result = await gmail.send_draft(
    draft_id=draft.gmail_draft_id,
)

        self._update_after_send(draft)

        return {
            "success": True,
            "draft_id": draft_id,
            "message": f"Draft {draft_id} successfully sent.",
            "gmail_message_id": send_result.get("id"),
        }


    async def save_draft(
        self,
        draft_id: int,
        user_id: int,
    ) -> dict[str, Any]:

        draft = self._load_draft(
            draft_id,
            user_id=user_id
        )
        gmail = await self._get_gmail_service(user_id)
        email = self._load_email(
    draft.email_id
)

        gmail_result = await gmail.create_draft(
    to=email.sender,
    subject=f"Re: {email.subject}",
    body=draft.draft,
    thread_id=email.gmail_thread_id,
)

        gmail_draft_id = gmail_result.get("id")

        if gmail_draft_id:
            self._update_after_save(
                draft,
                gmail_draft_id
            )

        return {
            "success": True,
            "draft_id": draft_id,
            "gmail_draft_id": gmail_draft_id,
            "message": f"Draft {draft_id} saved to Gmail."
        }


    async def update_draft(
        self,
        draft_id: int,
        user_id: int,
    ) -> dict[str, Any]:

        draft = self._load_draft(
            draft_id,
            user_id=user_id
        )

        gmail_draft_id = getattr(
            draft,
            "gmail_draft_id",
            None
        )

        if not gmail_draft_id:
            return await self.save_draft(
                draft_id,
                user_id
            )
        gmail = await self._get_gmail_service(user_id)

        email = self._load_email(
    draft.email_id
)

        gmail_result = await gmail.update_draft(
    draft_id=gmail_draft_id,
    to=email.sender,
    subject=f"Re: {email.subject}",
    body=draft.draft,
    thread_id=email.gmail_thread_id,
)


        return {
            "success": True,
            "draft_id": draft_id,
            "gmail_draft_id": gmail_result.get(
                "id",
                gmail_draft_id
            ),
            "message": f"Draft {draft_id} updated in Gmail."
        }



    def _ensure_approved(
        self,
        draft_id: int,
        user_id: int
    ):
        status = self.approval_service.get_status(
            draft_id,
            user_id=user_id
        )

        if status != "approved":
            raise ValueError(
                f"Draft {draft_id} cannot be sent. "
                f"Current status: {status}"
            )


    def _load_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> DraftReply:

        draft = self.draft_service.load_draft(
            draft_id,
            user_id=user_id
        )

        if draft is None:
            raise ValueError(
                f"Draft {draft_id} not found."
            )

        return draft



    def _update_after_send(
        self,
        draft: DraftReply
    ):

        if hasattr(draft, "is_sent"):
            draft.is_sent = True

        if hasattr(draft, "is_current"):
            draft.is_current = False

        self.db.commit()



    def _update_after_save(
        self,
        draft: DraftReply,
        gmail_draft_id: str
    ):

        if hasattr(
            draft,
            "gmail_draft_id"
        ):
            draft.gmail_draft_id = gmail_draft_id
            self.db.commit()