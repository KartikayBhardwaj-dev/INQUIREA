from __future__ import annotations

from typing import Any
from backend.app.services.approval_service import ApprovalService


class ApprovalTools:
    """
    Thin wrapper around ApprovalService.
    """

    def __init__(self, service: ApprovalService):
        self.service = service

    def approve_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> Any:
        return self.service.approve_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

    def reject_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> Any:
        return self.service.reject_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

    def reset_to_pending(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> Any:
        """
        Reset an approval state back to pending.
        """
        return self.service.reset_to_pending(
            draft_id=draft_id,
            user_id=user_id,
        )

    def get_status(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> str:
        return self.service.get_status(
            draft_id=draft_id,
            user_id=user_id,
        )