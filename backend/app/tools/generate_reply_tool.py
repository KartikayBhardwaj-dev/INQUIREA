from backend.app.tools.base_tool import BaseTool
from backend.app.services.draft_service import DraftService
from backend.app.tools.draft_tools import DraftTools


class GenerateReplyTool(BaseTool):

    name = "generate_reply"

    async def execute(
        self,
        **kwargs,
    ):
        db = kwargs.get("db")
        email_id = kwargs.get("email_id")
        user_id = kwargs.get("user_id")

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

        service = DraftService(db)

        tools = DraftTools(service)

        # -----------------------------------------------------
        # Generate only.
        #
        # This creates:
        #
        # DB Draft
        # +
        # PENDING approval
        #
        # It does NOT create a Gmail draft.
        # -----------------------------------------------------

        draft = await tools.generate_reply(
            email_id=email_id,
            tone=kwargs.get(
                "tone",
                "professional",
            ),
            user_id=user_id,
        )

        return {
            "draft_id": draft.id,
            "email_id": draft.email_id,
            "draft": draft.draft,
            "version": draft.version,
            "tone": draft.tone,
            "is_current": draft.is_current,
            "approval_status": "pending",
            "gmail_draft_id": draft.gmail_draft_id,
            "gmail_message_id": draft.gmail_message_id,
        }