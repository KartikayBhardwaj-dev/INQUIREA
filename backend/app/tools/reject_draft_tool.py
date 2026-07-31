from __future__ import annotations

from backend.app.services.approval_service import ApprovalService
from backend.app.tools.approval_tools import ApprovalTools
from backend.app.tools.base_tool import BaseTool


class RejectDraftTool(BaseTool):

    name = "reject_draft"

    async def execute(
        self,
        **kwargs,
    ):
        service = ApprovalService(
            kwargs["db"],
        )

        tools = ApprovalTools(
            service,
        )

        approval = tools.reject_draft(
            draft_id=kwargs["draft_id"],
            user_id=kwargs["user_id"]
        )

        return {
            "draft_id": approval.draft_reply_id,
            "status": approval.status,
            "rejected_at": approval.updated_at,
            "message": "Draft rejected successfully.",
        }