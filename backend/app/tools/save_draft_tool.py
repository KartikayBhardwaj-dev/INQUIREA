from backend.app.tools.base_tool import BaseTool
from backend.app.services.gmail_action_service import GmailActionService


class SaveDraftTool(BaseTool):

    name = "save_draft"

    async def execute(
        self,
        **kwargs,
    ):
        draft_id = kwargs.get(
            "draft_id"
        )

        user_id = kwargs.get(
            "user_id"
        )

        db = kwargs.get(
            "db"
        )

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

        return await service.save_draft(
            draft_id=draft_id,
            user_id=user_id,
        )