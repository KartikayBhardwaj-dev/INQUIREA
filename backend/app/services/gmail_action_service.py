from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.draft_reply import DraftReply
from backend.app.services.approval_service import ApprovalService
from backend.app.services.draft_service import DraftService
from backend.app.services.gmail_service import GmailService

logger = logging.getLogger(__name__)


class GmailActionService:
    """
    Gmail action orchestration service.

    Responsibilities
    ----------------
    - Validate approval state
    - Invoke Gmail API integration via GmailService
    - Persist synchronized Gmail identifiers to database
    """

    def __init__(self, db: Session):
        self.db = db
        self.gmail_service = GmailService(db)
        self.approval_service = ApprovalService(db)
        self.draft_service = DraftService(db)

    async def send_reply(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Send an approved draft email through Gmail API.
        """
        draft = self._load_draft(draft_id, user_id=user_id)
        self._ensure_approved(draft_id)

        # Dispatch outgoing email via Gmail service integration
        send_result = await self.gmail_service.send_email_reply(
            email_id=draft.email_id,
            body=draft.draft,
            user_id=user_id,
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
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Save/Create a draft into Gmail Drafts.
        """
        draft = self._load_draft(draft_id, user_id=user_id)

        gmail_result = await self.gmail_service.create_draft(
            email_id=draft.email_id,
            body=draft.draft,
            user_id=user_id,
        )

        gmail_draft_id = gmail_result.get("id")
        if gmail_draft_id:
            self._update_after_save(draft, str(gmail_draft_id))

        return {
            "success": True,
            "draft_id": draft_id,
            "gmail_draft_id": gmail_draft_id,
            "message": f"Draft {draft_id} saved to Gmail.",
        }

    async def update_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Update an existing draft in Gmail.
        """
        draft = self._load_draft(draft_id, user_id=user_id)
        gmail_draft_id = getattr(draft, "gmail_draft_id", None)

        if not gmail_draft_id:
            # Fall back to creating a new Gmail draft if no existing remote draft ID is recorded
            return await self.save_draft(draft_id, user_id=user_id)

        gmail_result = await self.gmail_service.update_draft(
            gmail_draft_id=gmail_draft_id,
            body=draft.draft,
            user_id=user_id,
        )

        return {
            "success": True,
            "draft_id": draft_id,
            "gmail_draft_id": gmail_result.get("id", gmail_draft_id),
            "message": f"Draft {draft_id} updated in Gmail.",
        }

    def _ensure_approved(self, draft_id: int) -> None:
        """
        Verify draft has been explicitly approved before execution.
        """
        status = self.approval_service.get_status(draft_id)
        if status != "approved":
            raise ValueError(
                f"Draft {draft_id} cannot be sent. Current approval status is '{status}'. "
                "The draft must be approved first."
            )

    def _load_draft(self, draft_id: int, user_id: int | None = None) -> DraftReply:
        """
        Load draft record from database.
        """
        draft = self.draft_service.load_draft(draft_id, user_id=user_id)
        if draft is None:
            raise ValueError(f"Draft with ID {draft_id} not found.")
        return draft

    def _update_after_send(self, draft: DraftReply) -> None:
        """
        Mark draft status as sent after successful dispatch.
        """
        if hasattr(draft, "is_sent"):
            setattr(draft, "is_sent", True)
        if hasattr(draft, "is_current"):
            setattr(draft, "is_current", False)
            
        self.db.commit()

    def _update_after_save(self, draft: DraftReply, gmail_draft_id: str) -> None:
        """
        Store Gmail draft identifier metadata locally.
        """
        if hasattr(draft, "gmail_draft_id"):
            setattr(draft, "gmail_draft_id", gmail_draft_id)
            self.db.commit()