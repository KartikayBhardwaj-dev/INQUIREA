from __future__ import annotations

from backend.app.services.draft_service import DraftService
from backend.app.tools.base_tool import BaseTool


class RewriteReplyTool(BaseTool):

    name = "rewrite_reply"

    async def execute(
        self,
        **kwargs,
    ):
        # =====================================================
        # VALIDATE INPUT
        # =====================================================

        draft_id = kwargs.get("draft_id")
        tone = kwargs.get(
            "tone",
            "professional",
        )
        instruction = kwargs.get("instruction")
        user_id = kwargs.get("user_id")
        db = kwargs.get("db")

        if draft_id is None:
            raise ValueError(
                "draft_id is required."
            )

        if instruction is None or not instruction.strip():
            raise ValueError(
                "instruction is required."
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
        # REWRITE
        # =====================================================

        service = DraftService(db)

        draft = await service.rewrite_draft(
            draft_id=draft_id,
            tone=tone,
            instruction=instruction.strip(),
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
            "tone": draft.tone,
            "is_current": draft.is_current,
            "approval_status": "pending",
            "message": "Draft rewritten.",
        }