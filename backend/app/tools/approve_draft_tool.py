from __future__ import annotations

from backend.app.services.approval_service import ApprovalService
from backend.app.tools.approval_tools import ApprovalTools
from backend.app.tools.base_tool import BaseTool


class ApproveDraftTool(BaseTool):

    name = "approve_draft"

    async def execute(
        self,
        **kwargs,
    ):
        # =====================================================
        # VALIDATE INPUT
        # =====================================================

        db = kwargs.get("db")
        draft_id = kwargs.get("draft_id")
        user_id = kwargs.get("user_id")

        if db is None:
            raise ValueError(
                "Database session missing."
            )

        if draft_id is None:
            raise ValueError(
                "draft_id is required."
            )

        if user_id is None:
            raise ValueError(
                "user_id is required."
            )

        # =====================================================
        # APPROVE DRAFT
        # =====================================================

        service = ApprovalService(db)

        tools = ApprovalTools(service)

        approval = tools.approve_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        # =====================================================
        # VERIFY APPROVAL
        # =====================================================

        if approval is None:
            raise ValueError(
                f"Approval for draft {draft_id} could not be created."
            )

        if approval.status != "approved":
            raise ValueError(
                f"Draft {draft_id} approval failed. "
                f"Current status: {approval.status}"
            )

        # =====================================================
        # RETURN FRONTEND-FRIENDLY RESPONSE
        # =====================================================

        return {
            "draft_id": approval.draft_reply_id,
            "approval_status": approval.status,
            "can_send": True,
            "message": "Draft approved successfully.",
        }