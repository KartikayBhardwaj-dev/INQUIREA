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

    Transaction rule:

        Validate DB
            ↓
        Call Gmail
            ↓
        Gmail succeeds
            ↓
        Update DB
            ↓
        flush()
            ↓
        commit()

        Exception
            ↓
        rollback()

    IMPORTANT:

    Gmail is an external system. A successful Gmail API call
    cannot be rolled back by SQLAlchemy.

    Therefore:

        Gmail operation MUST happen before DB state is marked
        as successful.

    This prevents the database from saying "sent" when Gmail
    actually failed.
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
        Save DB draft to Gmail.

        Existing Gmail draft:
            UPDATE

        No Gmail draft:
            CREATE

        DB is only updated after Gmail succeeds.
        """

        try:
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

            # -------------------------------------------------
            # Existing Gmail draft
            # -------------------------------------------------

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

                if not gmail_draft_id:
                    raise ValueError(
                        "Gmail did not return a draft ID "
                        "after updating the draft."
                    )

            # -------------------------------------------------
            # No Gmail draft → create
            # -------------------------------------------------

            else:

                gmail_result = await gmail.create_draft(
                    to=email.sender,
                    subject=f"Re: {email.subject}",
                    body=draft.draft,
                    thread_id=email.gmail_thread_id,
                )

                gmail_draft_id = gmail_result.get("id")

                if not gmail_draft_id:
                    raise ValueError(
                        "Gmail did not return a draft ID "
                        "after creating the draft."
                    )

            # -------------------------------------------------
            # Gmail succeeded.
            #
            # Only now update DB.
            # -------------------------------------------------

            draft.gmail_draft_id = gmail_draft_id

            self.db.flush()
            self.db.commit()

            self.db.refresh(draft)

            logger.info(
                "Draft %s saved to Gmail. Gmail draft ID=%s",
                draft.id,
                gmail_draft_id,
            )

            return {
                "success": True,
                "draft_id": draft.id,
                "gmail_draft_id": gmail_draft_id,
                "status": "saved",
                "message": "Draft saved to Gmail.",
            }

        except Exception:
            # If Gmail failed, any DB changes in this transaction
            # are discarded.
            self.db.rollback()
            raise

    # =========================================================
    # UPDATE DRAFT
    # =========================================================

    async def update_draft(
        self,
        draft_id: int,
        user_id: int,
    ) -> dict[str, Any]:
        """
        Synchronize current DB draft with Gmail.

        Existing gmail_draft_id:
            Gmail UPDATE

        Missing gmail_draft_id:
            Gmail CREATE

        DB changes are committed only after Gmail succeeds.
        """

        try:
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

            # -------------------------------------------------
            # Existing Gmail draft → UPDATE
            # -------------------------------------------------

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

                if not gmail_draft_id:
                    raise ValueError(
                        "Gmail did not return a draft ID "
                        "after updating."
                    )

            # -------------------------------------------------
            # No Gmail draft → CREATE
            # -------------------------------------------------

            else:

                gmail_result = await gmail.create_draft(
                    to=email.sender,
                    subject=f"Re: {email.subject}",
                    body=draft.draft,
                    thread_id=email.gmail_thread_id,
                )

                gmail_draft_id = gmail_result.get("id")

                if not gmail_draft_id:
                    raise ValueError(
                        "Gmail did not return a draft ID "
                        "after creating."
                    )

            # -------------------------------------------------
            # Gmail succeeded.
            # -------------------------------------------------

            draft.gmail_draft_id = gmail_draft_id

            self.db.flush()
            self.db.commit()

            self.db.refresh(draft)

            logger.info(
                "Updated/synchronized Gmail draft %s "
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

        except Exception:
            self.db.rollback()
            raise

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
            user owns draft
            +
            email belongs to user
            +
            draft is current
            +
            approval == approved
            +
            gmail_draft_id exists

        Gmail must successfully return a message ID before
        the DB is marked as SENT.
        """

        try:
            # -------------------------------------------------
            # 1. Load + ownership
            # -------------------------------------------------

            draft = self._load_draft(
                draft_id=draft_id,
                user_id=user_id,
            )

            # -------------------------------------------------
            # 2. Current version only
            # -------------------------------------------------

            if not draft.is_current:
                raise ValueError(
                    f"Draft {draft_id} cannot be sent. "
                    "It is not the current draft version."
                )

            # -------------------------------------------------
            # 3. Approval
            # -------------------------------------------------

            self._ensure_approved(
                draft_id=draft_id,
                user_id=user_id,
            )

            # -------------------------------------------------
            # 4. Gmail draft required
            # -------------------------------------------------

            if not draft.gmail_draft_id:
                raise ValueError(
                    f"Draft {draft_id} has no Gmail draft ID. "
                    "Save draft to Gmail first."
                )

            # -------------------------------------------------
            # 5. Gmail service
            # -------------------------------------------------

            gmail = await self._get_gmail_service(
                user_id=user_id,
            )

            # -------------------------------------------------
            # 6. IMPORTANT:
            #
            # Gmail send happens BEFORE any DB send-state
            # is persisted.
            # -------------------------------------------------

            send_result = await gmail.send_draft(
                draft_id=draft.gmail_draft_id,
            )

            gmail_message_id = send_result.get("id")

            if not gmail_message_id:
                raise ValueError(
                    "Gmail did not return a message ID "
                    "after sending."
                )

            # -------------------------------------------------
            # 7. Gmail succeeded.
            #
            # Now update DB.
            # -------------------------------------------------

            self._update_after_send(
    draft=draft,
    user_id=user_id,
    gmail_message_id=gmail_message_id,
)

# -------------------------------------------------
# DB state is now prepared successfully.
# Caller owns the transaction, so commit here.
# -------------------------------------------------

            self.db.commit()
            self.db.refresh(draft)

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

        except Exception:
            self.db.rollback()
            raise

    # =========================================================
    # APPROVAL VALIDATION
    # =========================================================

    def _ensure_approved(
        self,
        draft_id: int,
        user_id: int,
    ) -> None:

        draft = self._load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        approval = self.approval_service.load_approval(
            draft_id=draft.id,
        )

        status = (
            "pending"
            if approval is None
            else approval.status
        )

        if status != "approved":
            raise ValueError(
                f"Draft {draft_id} cannot be sent. "
                f"Current status: {status}"
            )

    # =========================================================
    # AFTER SEND
    # =========================================================

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
    Persist successful Gmail send state.

    IMPORTANT:
    This method does NOT commit.

    The caller owns the transaction.

    Gmail send succeeds
        ↓
    update DB state
        ↓
    flush()
        ↓
    caller commits
    """

        if draft.user_id != user_id:
            raise ValueError(
            "You do not own this draft."
        )

        draft.is_sent = True
        draft.gmail_message_id = gmail_message_id
        draft.sent_at = datetime.utcnow()
        draft.is_current = False

    # Flush only.
    #
    # send_reply() owns the transaction and
    # performs the final commit.
        self.db.flush()

        logger.info(
        "Prepared sent state for Draft %s. "
        "Gmail message ID=%s sent_at=%s",
        draft.id,
        draft.gmail_message_id,
        draft.sent_at,
    )