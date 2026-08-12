from __future__ import annotations

from backend.app.services.gmail_action_service import GmailActionService
from backend.app.tools.base_tool import BaseTool


class SaveDraftTool(BaseTool):

    name = "save_draft"

    async def execute(
        self,
        **kwargs,
    ):
        # =====================================================
        # VALIDATE INPUT
        # =====================================================

        draft_id = kwargs.get("draft_id")
        user_id = kwargs.get("user_id")
        db = kwargs.get("db")

        if draft_id is None:
            raise ValueError(
                "draft_id is required."
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
        # SAVE / UPDATE GMAIL DRAFT
        # =====================================================

        service = GmailActionService(db)

        result = await service.save_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        # =====================================================
        # FRONTEND RESPONSE
        # =====================================================

        return {
            "draft_id": result["draft_id"],
            "gmail_draft_id": result["gmail_draft_id"],
            "status": "saved",
            "message": "Draft saved to Gmail.",
        }