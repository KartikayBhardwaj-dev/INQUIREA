from __future__ import annotations

from backend.app.services.draft_service import DraftService
from backend.app.tools.base_tool import BaseTool
from backend.app.tools.draft_tools import DraftTools


class GenerateReplyTool(BaseTool):

    name = "generate_reply"

    async def execute(
        self,
        **kwargs,
    ):
        # =====================================================
        # VALIDATE INPUT
        # =====================================================

        db = kwargs.get("db")
        email_id = kwargs.get("email_id")
        user_id = kwargs.get("user_id")
        tone = kwargs.get(
            "tone",
            "professional",
        )

        if db is None:
            raise ValueError(
                "Database session missing."
            )

        if email_id is None:
            raise ValueError(
                "email_id is required."
            )

        if user_id is None:
            raise ValueError(
                "user_id is required."
            )

        # =====================================================
        # GENERATE DATABASE DRAFT
        # =====================================================

        service = DraftService(db)

        tools = DraftTools(service)

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # generate_reply:
        #
        #   AI generation
        #       ↓
        #   DB draft
        #       ↓
        #   pending approval
        #
        # It MUST NOT:
        #
        #   - create Gmail draft
        #   - update Gmail
        #   - send Gmail
        # -----------------------------------------------------

        draft = await tools.generate_reply(
            email_id=email_id,
            tone=tone,
            user_id=user_id,
        )

        # =====================================================
        # RETURN FRONTEND-FRIENDLY RESULT
        # =====================================================

        return {
            "draft_id": draft.id,
            "email_id": draft.email_id,
            "draft": draft.draft,
            "version": draft.version,
            "tone": draft.tone,
            "is_current": draft.is_current,
            "approval_status": "pending",
        }