from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.draft_reply import DraftReply
from backend.app.models.email import Email
from backend.app.models.users import User
from backend.app.services.approval_service import ApprovalService
from backend.app.services.draft_service import DraftService
from backend.app.services.gmail_service import GmailService
from backend.app.services.google_token_service import GoogleTokenService

logger = logging.getLogger(__name__)


class GmailActionService:
    """
    Gmail action orchestration service.

    All operations enforce:

        draft.user_id == authenticated user_id

    and

        email.user_id == authenticated user_id
    """

    def __init__(self, db: Session):
        self.db = db
        self.approval_service = ApprovalService(db)
        self.draft_service = DraftService(db)

    # =========================================================
    # GMAIL SERVICE
    # =========================================================

    async def _get_gmail_service(
        self,
        user_id: int,
    ) -> GmailService:

        user = (
            self.db.query(User)
            .filter(
                User.id == user_id
            )
            .first()
        )

        if user is None:
            raise ValueError(
                "User not found."
            )

        access_token = (
            await GoogleTokenService.refresh_access_token(
                user=user,
                db=self.db,
            )
        )

        return GmailService(access_token)

    # =========================================================
    # EMAIL OWNERSHIP
    # =========================================================

    def _load_email(
        self,
        email_id: int,
        user_id: int,
    ) -> Email:

        email = (
            self.db.query(Email)
            .filter(
                Email.id == email_id,
                Email.user_id == user_id,
            )
            .first()
        )

        if email is None:
            raise ValueError(
                f"Email {email_id} not found "
                f"for user {user_id}."
            )

        return email

    # =========================================================
    # DRAFT OWNERSHIP
    # =========================================================

    def _load_draft(
        self,
        draft_id: int,
        user_id: int,
    ) -> DraftReply:

        draft = self.draft_service.load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft {draft_id} not found "
                f"for user {user_id}."
            )

        # -----------------------------------------------------
        # Defense-in-depth:
        # Ensure the email also belongs to the same user.
        # -----------------------------------------------------

        self._load_email(
            email_id=draft.email_id,
            user_id=user_id,
        )

        return draft

    # =========================================================
    # SEND REPLY
    # =========================================================

    async def send_reply(
        self,
        draft_id: int,
        user_id: int,
    ) -> dict[str, Any]:

        draft = self._load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        self._ensure_approved(
            draft_id=draft_id,
            user_id=user_id,
        )

        if not draft.gmail_draft_id:
            raise ValueError(
                f"Draft {draft_id} has no Gmail draft ID. "
                "Save draft to Gmail first."
            )

        gmail = await self._get_gmail_service(
            user_id
        )

        send_result = await gmail.send_draft(
            draft_id=draft.gmail_draft_id,
        )

        self._update_after_send(
            draft=draft,
            user_id=user_id,
        )

        return {
            "success": True,
            "draft_id": draft_id,
            "message": (
                f"Draft {draft_id} successfully sent."
            ),
            "gmail_message_id": send_result.get("id"),
        }

    # =========================================================
    # SAVE TO GMAIL
    # =========================================================

    async def save_draft(
        self,
        draft_id: int,
        user_id: int,
    ) -> dict[str, Any]:

        draft = self._load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        email = self._load_email(
            email_id=draft.email_id,
            user_id=user_id,
        )

        gmail = await self._get_gmail_service(
            user_id
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
                draft=draft,
                gmail_draft_id=gmail_draft_id,
                user_id=user_id,
            )

        return {
            "success": True,
            "draft_id": draft_id,
            "gmail_draft_id": gmail_draft_id,
            "message": (
                f"Draft {draft_id} saved to Gmail."
            ),
        }

    # =========================================================
    # UPDATE GMAIL DRAFT
    # =========================================================

    async def update_draft(
        self,
        draft_id: int,
        user_id: int,
    ) -> dict[str, Any]:

        draft = self._load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        gmail_draft_id = draft.gmail_draft_id

        # -----------------------------------------------------
        # If no Gmail draft exists, create one.
        # -----------------------------------------------------

        if not gmail_draft_id:
            return await self.save_draft(
                draft_id=draft_id,
                user_id=user_id,
            )

        email = self._load_email(
            email_id=draft.email_id,
            user_id=user_id,
        )

        gmail = await self._get_gmail_service(
            user_id
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
                gmail_draft_id,
            ),
            "message": (
                f"Draft {draft_id} updated in Gmail."
            ),
        }

    # =========================================================
    # APPROVAL
    # =========================================================

    def _ensure_approved(
        self,
        draft_id: int,
        user_id: int,
    ) -> None:

        status = self.approval_service.get_status(
            draft_id=draft_id,
            user_id=user_id,
        )

        if status != "approved":
            raise ValueError(
                f"Draft {draft_id} cannot be sent. "
                f"Current status: {status}."
            )

    # =========================================================
    # AFTER SEND
    # =========================================================

    def _update_after_send(
        self,
        draft: DraftReply,
        user_id: int,
    ) -> None:

        # Defense-in-depth ownership check.
        if draft.user_id != user_id:
            raise ValueError(
                "You do not own this draft."
            )

        draft.is_sent = True
        draft.is_current = False

        self.db.commit()

    # =========================================================
    # AFTER SAVE
    # =========================================================

    def _update_after_save(
        self,
        draft: DraftReply,
        gmail_draft_id: str,
        user_id: int,
    ) -> None:

        if draft.user_id != user_id:
            raise ValueError(
                "You do not own this draft."
            )

        draft.gmail_draft_id = gmail_draft_id

        self.db.commit()