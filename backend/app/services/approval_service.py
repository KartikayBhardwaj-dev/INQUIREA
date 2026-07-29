from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.app.models.approval import Approval
from backend.app.models.draft_reply import DraftReply

logger = logging.getLogger(__name__)


class ApprovalService:
    """
    Approval management service.

    Responsibilities
    ----------------
    - Approve draft
    - Reject draft
    - Get approval status
    - Validate approval transitions
    - Load approval records
    """

    def __init__(self, db: Session):
        self.db = db

    def load_approval(self, draft_id: int) -> Approval | None:
        return (
            self.db.query(Approval)
            .filter(Approval.draft_reply_id == draft_id)
            .first()
        )

    def load_draft(self, draft_id: int, user_id: int | None = None) -> DraftReply | None:
        query = self.db.query(DraftReply).filter(DraftReply.id == draft_id)
        if user_id is not None and hasattr(DraftReply, "user_id"):
            query = query.filter(DraftReply.user_id == user_id)
        return query.first()

    def approve_draft(self, draft_id: int, user_id: int | None = None) -> Approval:
        draft = self.load_draft(draft_id, user_id=user_id)
        if draft is None:
            raise ValueError(f"Draft with ID {draft_id} not found.")

        approval = self.load_approval(draft_id)
        if approval is None:
            approval = Approval(draft_reply_id=draft_id, status="pending")
            self.db.add(approval)
            self.db.flush()

        self._validate_transition(approval.status, "approved")
        approval.status = "approved"

        self.db.commit()
        self.db.refresh(approval)

        logger.info("Draft %s approved.", draft_id)
        return approval

    def reject_draft(self, draft_id: int, user_id: int | None = None) -> Approval:
        draft = self.load_draft(draft_id, user_id=user_id)
        if draft is None:
            raise ValueError(f"Draft with ID {draft_id} not found.")

        approval = self.load_approval(draft_id)
        if approval is None:
            approval = Approval(draft_reply_id=draft_id, status="pending")
            self.db.add(approval)
            self.db.flush()

        self._validate_transition(approval.status, "rejected")
        approval.status = "rejected"

        self.db.commit()
        self.db.refresh(approval)

        logger.info("Draft %s rejected.", draft_id)
        return approval

    def get_status(self, draft_id: int, user_id: int | None = None) -> str:
        draft = self.load_draft(draft_id, user_id=user_id)
        if draft is None:
            raise ValueError(f"Draft with ID {draft_id} not found.")

        approval = self.load_approval(draft_id)
        if approval is None:
            return "pending"

        return approval.status

    def _validate_transition(self, current_status: str, new_status: str) -> None:
        if current_status == new_status:
            raise ValueError(f"Draft is already {current_status}.")

        if current_status not in {"pending", "approved", "rejected"}:
            raise ValueError(f"Invalid current approval status: '{current_status}'.")

    def reset_to_pending(self, draft_id: int, user_id: int | None = None) -> Approval:
        draft = self.load_draft(draft_id, user_id=user_id)
        if draft is None:
            raise ValueError(f"Draft with ID {draft_id} not found.")

        approval = self.load_approval(draft_id)
        if approval is None:
            approval = Approval(draft_reply_id=draft_id, status="pending")
            self.db.add(approval)
        else:
            approval.status = "pending"

        self.db.commit()
        self.db.refresh(approval)

        logger.info("Draft %s reset to pending.", draft_id)
        return approval