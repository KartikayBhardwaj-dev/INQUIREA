from backend.app.tools.base_tool import BaseTool

from backend.app.database.session import SessionLocal
from backend.app.services.gmail_action_service import GmailActionService


class UpdateDraftTool(BaseTool):

    name = "update_draft"

    async def execute(self, **kwargs):

        draft_id = kwargs.get("draft_id")

        if draft_id is None:
            raise ValueError("draft_id is required.")

        db = SessionLocal()

        try:
            service = GmailActionService(db)

            result = await service.update_draft(
                draft_id=draft_id,
            )

            return result

        finally:
            db.close()