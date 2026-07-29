from __future__ import annotations

from backend.app.services.approval_service import ApprovalService
from backend.app.services.draft_service import DraftService
from backend.app.tools.base_tool import BaseTool


class EditDraftTool(BaseTool):

    name = "edit_draft"

    async def execute(
        self,
        **kwargs,
    ):
        draft_service = DraftService(
            kwargs["db"],
        )

        approval_service = ApprovalService(
            kwargs["db"],
        )

        draft = draft_service.save_draft(
            draft_id=kwargs["draft_id"],
            content=kwargs["content"],
        )

        approval = approval_service.reset_to_pending(
            draft_id=draft.id,
        )

        return {
            "draft_id": draft.id,
            "email_id": draft.email_id,
            "draft": draft.draft,
            "status": approval.status,
            "message": "Draft updated and approval reset to pending.",
        }