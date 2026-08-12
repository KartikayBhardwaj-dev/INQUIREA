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
        # =====================================================
        # VALIDATE INPUT
        # =====================================================

        draft_id = kwargs.get("draft_id")
        content = kwargs.get("content")
        user_id = kwargs.get("user_id")
        db = kwargs.get("db")

        if draft_id is None:
            raise ValueError(
                "draft_id is required."
            )

        if content is None:
            raise ValueError(
                "content is required."
            )

        if user_id is None:
            raise ValueError(
                "user_id is required."
            )

        if db is None:
            raise ValueError(
                "Database session missing."
            )

        # =====================================================
        # UPDATE DRAFT
        # =====================================================

        draft_service = DraftService(db)

        draft = draft_service.save_draft(
            draft_id=draft_id,
            content=content,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft {draft_id} not found."
            )

        # =====================================================
        # RESET APPROVAL
        # =====================================================

        approval_service = ApprovalService(db)

        approval = approval_service.reset_to_pending(
            draft_id=draft.id,
            user_id=user_id,
        )

        # =====================================================
        # RESPONSE
        # =====================================================

        return {
            "draft_id": draft.id,
            "email_id": draft.email_id,
            "draft": draft.draft,
            "approval_status": approval.status,
            "message": "Draft updated.",
        }