from __future__ import annotations

from backend.app.services.gmail_action_service import GmailActionService
from backend.app.tools.base_tool import BaseTool


class SendReplyTool(BaseTool):

    name = "send_reply"

    async def execute(
        self,
        **kwargs,
    ):
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

        service = GmailActionService(
            db=db,
        )

        result = await service.send_reply(
            draft_id=draft_id,
            user_id=user_id,
        )

        return {
            "draft_id": result["draft_id"],
            "status": "sent",
            "gmail_message_id": result["gmail_message_id"],
            "message": "Email sent successfully.",
        }