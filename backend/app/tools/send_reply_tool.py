from __future__ import annotations

from backend.app.services.gmail_action_service import GmailActionService
from backend.app.tools.base_tool import BaseTool


class SendReplyTool(BaseTool):

    name = "send_reply"

    async def execute(
        self,
        **kwargs,
    ):
        # -----------------------------------------------------
        # Validate required inputs
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Send through GmailActionService.
        #
        # IMPORTANT:
        # All security checks happen inside
        # GmailActionService.send_reply():
        #
        # 1. Draft exists
        # 2. Draft belongs to user
        # 3. Email belongs to user
        # 4. Draft is current
        # 5. Approval exists
        # 6. Approval == approved
        # 7. Gmail draft ID exists
        # 8. Gmail send succeeds
        #
        # The tool itself must NOT bypass any of these checks.
        # -----------------------------------------------------

        service = GmailActionService(
            db=db,
        )

        result = await service.send_reply(
            draft_id=draft_id,
            user_id=user_id,
        )

        # -----------------------------------------------------
        # Return frontend-friendly response
        # -----------------------------------------------------

        return {
            "draft_id": result["draft_id"],
            "status": "sent",
            "gmail_message_id": result["gmail_message_id"],
            "message": "Email sent successfully.",
        }