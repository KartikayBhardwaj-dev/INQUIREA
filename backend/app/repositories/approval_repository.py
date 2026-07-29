from __future__ import annotations

import logging
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.approval import Approval, ApprovalStatus

logger = logging.getLogger(__name__)


class ApprovalRepository:
    """
    Database Access Layer for Approval entity.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_approval_request(
        self,
        draft_reply_id: int,
        status: str = ApprovalStatus.PENDING.value,
    ) -> Approval:
        try:
            approval = Approval(
                draft_reply_id=draft_reply_id,
                status=status,
            )
            self.db.add(approval)
            self.db.flush()
            logger.info("Created Approval ID %s for DraftReply ID %s", approval.id, draft_reply_id)
            return approval
        except SQLAlchemyError:
            logger.exception("Failed to create Approval request for DraftReply ID %s", draft_reply_id)
            raise

    def get_by_id(self, approval_id: int) -> Optional[Approval]:
        return self.db.query(Approval).filter(Approval.id == approval_id).first()

    def get_by_draft_id(self, draft_reply_id: int) -> Optional[Approval]:
        return (
            self.db.query(Approval)
            .filter(Approval.draft_reply_id == draft_reply_id)
            .first()
        )

    def update_status(
        self,
        draft_reply_id: int,
        status: str,
    ) -> Optional[Approval]:
        approval = self.get_by_draft_id(draft_reply_id)
        if not approval:
            logger.warning("Attempted status update on non-existent Approval for DraftReply ID %s", draft_reply_id)
            return None

        try:
            approval.status = status
            self.db.flush()
            logger.info("Updated Approval for DraftReply ID %s status to '%s'", draft_reply_id, status)
            return approval
        except SQLAlchemyError:
            logger.exception("Failed to update status for DraftReply ID %s", draft_reply_id)
            raise

    def approve_request(self, draft_reply_id: int) -> Optional[Approval]:
        return self.update_status(draft_reply_id, ApprovalStatus.APPROVED.value)

    def reject_request(self, draft_reply_id: int) -> Optional[Approval]:
        return self.update_status(draft_reply_id, ApprovalStatus.REJECTED.value)

    def delete_approval(self, approval_id: int) -> bool:
        approval = self.get_by_id(approval_id)
        if not approval:
            return False

        try:
            self.db.delete(approval)
            self.db.flush()
            logger.info("Deleted Approval ID %s", approval_id)
            return True
        except SQLAlchemyError:
            logger.exception("Failed to delete Approval ID %s", approval_id)
            raise