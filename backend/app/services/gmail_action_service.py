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

    Security invariants
    -------------------
    1. Draft must belong to the authenticated user.
    2. Email must belong to the authenticated user.
    3. Approval must exist.
    4. Draft approval status must be APPROVED before sending.
    5. Draft must have a Gmail draft ID before sending.
    6. Only the current draft version can be sent.
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
            .filter(User.id == user_id)
            .first()
        )

        if user is None:
            raise ValueError("User not found.")

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
        """
        Load an email only if it belongs to the authenticated user.
        """

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
                f"Email {email_id} not found."
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
        """
        Load a draft only if:

        - draft belongs to user
        - associated email belongs to user
        """

        draft = self.draft_service.load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft {draft_id} not found."
            )

        # Defense-in-depth ownership validation.
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
        """
        Send a draft through Gmail.

        A draft can ONLY be sent when:

            draft exists
            +
            draft belongs to user
            +
            email belongs to user
            +
            draft is current
            +
            approval exists
            +
            approval == approved
            +
            Gmail draft ID exists
        """

        # -----------------------------------------------------
        # 1. Validate draft + ownership
        # -----------------------------------------------------

        draft = self._load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        # -----------------------------------------------------
        # 2. Only current version may be sent
        # -----------------------------------------------------

        if not draft.is_current:
            raise ValueError(
                f"Draft {draft_id} cannot be sent. "
                "It is not the current draft version."
            )

        # -----------------------------------------------------
        # 3. Approval is mandatory
        # -----------------------------------------------------

        self._ensure_approved(
            draft_id=draft_id,
            user_id=user_id,
        )

        # -----------------------------------------------------
        # 4. Gmail draft must exist
        # -----------------------------------------------------

        if not draft.gmail_draft_id:
            raise ValueError(
                f"Draft {draft_id} has no Gmail draft ID. "
                "Save draft to Gmail first."
            )

        # -----------------------------------------------------
        # 5. Get authenticated user's Gmail service
        # -----------------------------------------------------

        gmail = await self._get_gmail_service(
            user_id=user_id,
        )

        # -----------------------------------------------------
        # 6. Send Gmail draft
        # -----------------------------------------------------

        send_result = await gmail.send_draft(
            draft_id=draft.gmail_draft_id,
        )

        # -----------------------------------------------------
        # 7. Mark database state as sent
        # -----------------------------------------------------

        self._update_after_send(
            draft=draft,
            user_id=user_id,
        )

        logger.info(
            "Draft %s successfully sent by user %s.",
            draft_id,
            user_id,
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
        """
        Save the user's draft to Gmail.

        Approval is NOT required to save a Gmail draft.

        Approval is required only when sending.
        """

        draft = self._load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        email = self._load_email(
            email_id=draft.email_id,
            user_id=user_id,
        )

        gmail = await self._get_gmail_service(
            user_id=user_id,
        )

        gmail_result = await gmail.create_draft(
            to=email.sender,
            subject=f"Re: {email.subject}",
            body=draft.draft,
            thread_id=email.gmail_thread_id,
        )

        gmail_draft_id = gmail_result.get("id")

        if not gmail_draft_id:
            raise ValueError(
                "Gmail did not return a draft ID."
            )

        self._update_after_save(
            draft=draft,
            gmail_draft_id=gmail_draft_id,
            user_id=user_id,
        )

        logger.info(
            "Draft %s saved to Gmail by user %s.",
            draft_id,
            user_id,
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
        """
        Update an existing Gmail draft.

        Approval is not required for updating the Gmail draft.

        However, sending still requires APPROVED status.
        """

        draft = self._load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        gmail_draft_id = draft.gmail_draft_id

        # -----------------------------------------------------
        # If Gmail draft does not exist, create it.
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
            user_id=user_id,
        )

        gmail_result = await gmail.update_draft(
            draft_id=gmail_draft_id,
            to=email.sender,
            subject=f"Re: {email.subject}",
            body=draft.draft,
            thread_id=email.gmail_thread_id,
        )

        logger.info(
            "Gmail draft %s updated by user %s.",
            gmail_draft_id,
            user_id,
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
    # APPROVAL VALIDATION
    # =========================================================

    def _ensure_approved(
        self,
        draft_id: int,
        user_id: int,
    ) -> None:
        """
        Absolute backend invariant for sending.

        Only:

            approval.status == "approved"

        is allowed.

        Missing approval is treated as pending.
        """

        # -----------------------------------------------------
        # First ensure the draft belongs to the user.
        # -----------------------------------------------------

        draft = self._load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        # -----------------------------------------------------
        # Load approval.
        # -----------------------------------------------------

        approval = self.approval_service.load_approval(
            draft_id=draft.id,
        )

        # -----------------------------------------------------
        # Missing approval = pending.
        # -----------------------------------------------------

        if approval is None:
            status = "pending"
        else:
            status = approval.status

        # -----------------------------------------------------
        # ONLY approved is allowed.
        # -----------------------------------------------------

        if status != "approved":
            raise ValueError(
                f"Draft {draft_id} cannot be sent. "
                f"Current status: {status}"
            )

    # =========================================================
    # AFTER SEND
    # =========================================================

    def _update_after_send(
        self,
        draft: DraftReply,
        user_id: int,
    ) -> None:
        """
        Update database after successful Gmail send.
        """

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
        """
        Store Gmail draft ID after successful Gmail creation.
        """

        # Defense-in-depth ownership check.
        if draft.user_id != user_id:
            raise ValueError(
                "You do not own this draft."
            )

        draft.gmail_draft_id = gmail_draft_id

        self.db.commit()