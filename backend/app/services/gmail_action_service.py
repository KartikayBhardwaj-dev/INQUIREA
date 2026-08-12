from __future__ import annotations

import logging
from datetime import datetime
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

    Lifecycle:

        Generate
            ↓
        DB Draft
            ↓
        Edit DB Draft
            ↓
        Save / Update Gmail Draft
            ↓
        Approve
            ↓
        Send
            ↓
        is_sent = True
        gmail_message_id = Gmail message ID
        sent_at = current time
        is_current = False

    Security invariants:

        1. Draft belongs to authenticated user.
        2. Email belongs to authenticated user.
        3. Only current draft can be sent.
        4. Approval must exist and be APPROVED.
        5. Gmail draft must exist before sending.
        6. Gmail message ID must be returned before marking
           the draft as sent.
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
                User.id == user_id,
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

        return GmailService(
            access_token,
        )

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

        draft = self.draft_service.load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft {draft_id} not found."
            )

        # Defense-in-depth:
        # Ensure the associated email belongs
        # to the same authenticated user.
        self._load_email(
            email_id=draft.email_id,
            user_id=user_id,
        )

        return draft

    # =========================================================
    # SAVE DRAFT TO GMAIL
    # =========================================================

    async def save_draft(
    self,
    draft_id: int,
    user_id: int,
) -> dict[str, Any]:
        """
    Save the current DB draft to Gmail.

    Lifecycle:

        No gmail_draft_id
            ↓
        Create Gmail draft

        Existing gmail_draft_id
            ↓
        Update existing Gmail draft

    Never create duplicate Gmail drafts.
    """

    # =========================================================
    # LOAD + OWNERSHIP
    # =========================================================

        draft = self._load_draft(
        draft_id=draft_id,
        user_id=user_id,
    )

        email = self._load_email(
        email_id=draft.email_id,
        user_id=user_id,
    )

    # =========================================================
    # GMAIL SERVICE
    # =========================================================

        gmail = await self._get_gmail_service(
        user_id=user_id,
    )

    # =========================================================
    # EXISTING GMAIL DRAFT
    # =========================================================

        if draft.gmail_draft_id:

            gmail_result = await gmail.update_draft(
            draft_id=draft.gmail_draft_id,
            to=email.sender,
            subject=f"Re: {email.subject}",
            body=draft.draft,
            thread_id=email.gmail_thread_id,
        )

            gmail_draft_id = gmail_result.get(
            "id",
            draft.gmail_draft_id,
        )

            draft.gmail_draft_id = gmail_draft_id

            self.db.commit()
            self.db.refresh(draft)

            logger.info(
            "Updated existing Gmail draft %s "
            "from DB draft %s.",
            gmail_draft_id,
            draft.id,
        )

            return {
            "success": True,
            "draft_id": draft.id,
            "gmail_draft_id": gmail_draft_id,
            "status": "saved",
            "message": "Draft saved to Gmail.",
        }

    # =========================================================
    # NO GMAIL DRAFT YET → CREATE ONE
    # =========================================================

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

        draft.gmail_draft_id = gmail_draft_id

        self.db.commit()
        self.db.refresh(draft)

        logger.info(
        "Created Gmail draft %s "
        "from DB draft %s.",
        gmail_draft_id,
        draft.id,
    )

        return {
        "success": True,
        "draft_id": draft.id,
        "gmail_draft_id": gmail_draft_id,
        "status": "saved",
        "message": "Draft saved to Gmail.",
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
    Synchronize the current DB draft with Gmail.

    Existing Gmail draft:
        DB draft
            ↓
        Gmail UPDATE

    No Gmail draft:
        DB draft
            ↓
        Gmail CREATE
    """

    # =========================================================
    # LOAD DB DRAFT + OWNERSHIP
    # =========================================================

        draft = self._load_draft(
        draft_id=draft_id,
        user_id=user_id,
    )

        email = self._load_email(
        email_id=draft.email_id,
        user_id=user_id,
    )

    # =========================================================
    # GET GMAIL SERVICE
    # =========================================================

        gmail = await self._get_gmail_service(
        user_id=user_id,
    )

    # =========================================================
    # EXISTING GMAIL DRAFT → UPDATE
    # =========================================================

        if draft.gmail_draft_id:

            gmail_result = await gmail.update_draft(
            draft_id=draft.gmail_draft_id,
            to=email.sender,
            subject=f"Re: {email.subject}",
            body=draft.draft,
            thread_id=email.gmail_thread_id,
        )

            gmail_draft_id = gmail_result.get(
            "id",
            draft.gmail_draft_id,
        )

            draft.gmail_draft_id = gmail_draft_id

            self.db.commit()
            self.db.refresh(draft)

            logger.info(
            "Updated Gmail draft %s "
            "from DB draft %s.",
            gmail_draft_id,
            draft.id,
        )

            return {
            "success": True,
            "draft_id": draft.id,
            "gmail_draft_id": gmail_draft_id,
            "status": "updated",
        }

    # =========================================================
    # NO GMAIL DRAFT → CREATE
    # =========================================================

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

        draft.gmail_draft_id = gmail_draft_id

        self.db.commit()
        self.db.refresh(draft)

        logger.info(
        "Created Gmail draft %s "
        "from DB draft %s.",
        gmail_draft_id,
        draft.id,
    )

        return {
        "success": True,
        "draft_id": draft.id,
        "gmail_draft_id": gmail_draft_id,
        "status": "updated",
    }

    # =========================================================
    # SEND REPLY
    # =========================================================

    async def send_reply(
        self,
        draft_id: int,
        user_id: int,
    ) -> dict[str, Any]:
        """
        Send an approved Gmail draft.

        Required:

            draft exists
            +
            correct owner
            +
            current version
            +
            approval == approved
            +
            Gmail draft exists

        After successful Gmail send:

            is_sent = True
            gmail_message_id = Gmail message ID
            sent_at = current timestamp
            is_current = False
        """

        # -----------------------------------------------------
        # 1. Load draft and validate ownership.
        # -----------------------------------------------------

        draft = self._load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        # -----------------------------------------------------
        # 2. Prevent sending old/superseded versions.
        # -----------------------------------------------------

        if not draft.is_current:
            raise ValueError(
                f"Draft {draft_id} cannot be sent. "
                "It is not the current draft version."
            )

        # -----------------------------------------------------
        # 3. Approval is mandatory.
        # -----------------------------------------------------

        self._ensure_approved(
            draft_id=draft_id,
            user_id=user_id,
        )

        # -----------------------------------------------------
        # 4. Gmail draft must exist.
        # -----------------------------------------------------

        if not draft.gmail_draft_id:
            raise ValueError(
                f"Draft {draft_id} has no Gmail draft ID. "
                "Save draft to Gmail first."
            )

        # -----------------------------------------------------
        # 5. Get authenticated Gmail service.
        # -----------------------------------------------------

        gmail = await self._get_gmail_service(
            user_id=user_id,
        )

        # -----------------------------------------------------
        # 6. Send Gmail draft.
        #
        # IMPORTANT:
        # Do NOT update the DB before this succeeds.
        # -----------------------------------------------------

        send_result = await gmail.send_draft(
            draft_id=draft.gmail_draft_id,
        )

        # -----------------------------------------------------
        # 7. Gmail must return the sent message ID.
        # -----------------------------------------------------

        gmail_message_id = send_result.get(
            "id"
        )

        if not gmail_message_id:
            raise ValueError(
                "Gmail did not return a message ID "
                "after sending."
            )

        # -----------------------------------------------------
        # 8. Persist successful send state.
        # -----------------------------------------------------

        self._update_after_send(
            draft=draft,
            user_id=user_id,
            gmail_message_id=gmail_message_id,
        )

        logger.info(
            "Draft %s sent successfully by user %s. "
            "Gmail message ID=%s",
            draft_id,
            user_id,
            gmail_message_id,
        )

        return {
            "success": True,
            "draft_id": draft_id,
            "gmail_message_id": gmail_message_id,
            "message": (
                f"Draft {draft_id} successfully sent."
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
        Absolute backend invariant:

        ONLY approved drafts can be sent.
        """

        # Defense-in-depth ownership validation.
        draft = self._load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        approval = self.approval_service.load_approval(
            draft_id=draft.id,
        )

        # Missing approval = pending.
        if approval is None:
            status = "pending"
        else:
            status = approval.status

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
        gmail_message_id: str,
    ) -> None:
        """
        Persist the successful Gmail send.

        Database state becomes:

            is_sent = True
            gmail_message_id = <Gmail message ID>
            sent_at = current UTC time
            is_current = False
        """

        # -----------------------------------------------------
        # Defense-in-depth ownership check.
        # -----------------------------------------------------

        if draft.user_id != user_id:
            raise ValueError(
                "You do not own this draft."
            )

        # -----------------------------------------------------
        # Persist send state.
        # -----------------------------------------------------

        draft.is_sent = True
        draft.gmail_message_id = gmail_message_id
        draft.sent_at = datetime.utcnow()
        draft.is_current = False

        # -----------------------------------------------------
        # Commit transaction.
        # -----------------------------------------------------

        self.db.commit()
        self.db.refresh(draft)

        logger.info(
            "Persisted sent state for draft %s. "
            "gmail_message_id=%s sent_at=%s",
            draft.id,
            draft.gmail_message_id,
            draft.sent_at,
        )