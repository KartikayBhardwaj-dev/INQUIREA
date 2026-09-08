from __future__ import annotations

from backend.app.services.draft_service import DraftService
from backend.app.services.approval_service import ApprovalService
from backend.app.tools.base_tool import BaseTool


class EditDraftTool(BaseTool):

    name = "edit_draft"

    async def execute(
        self,
        **kwargs,
    ):
        draft_id = kwargs.get("draft_id")
        content = kwargs.get("content")
        user_id = kwargs.get("user_id")
        db = kwargs.get("db")

        # =====================================================
        # VALIDATE INPUT
        # =====================================================

        if draft_id is None:
            raise ValueError(
                "draft_id is required."
            )

        if content is None or not content.strip():
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
        # EDIT DRAFT
        # =====================================================

        service = DraftService(db)

        draft = service.version_draft(
            draft_id=draft_id,
            content=content.strip(),
            user_id=user_id,
        )

        # save_draft() already resets approval to PENDING.

        approval_service = ApprovalService(db)

        approval_status = approval_service.get_status(
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
            "version": draft.version,
            "is_current": draft.is_current,
            "approval_status": approval_status,
            "message": "Draft updated.",
        }