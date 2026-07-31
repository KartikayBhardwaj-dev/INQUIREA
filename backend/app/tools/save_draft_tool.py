from backend.app.tools.base_tool import BaseTool
from sqlalchemy.orm import Session
from backend.app.services.gmail_action_service import GmailActionService
from backend.app.services.draft_service import DraftService
from backend.app.tools.draft_tools import DraftTools

# class SaveDraftTool(BaseTool):

#     name = "save_draft"

#     async def execute(self,db: Session **kwargs):
#         tools = DraftTools(
#             DraftService(db),
#         )
#         return {
#             "status": "not_implemented",
#             "message": "Save draft placeholder.",
#             "draft": kwargs,
#         }


class SaveDraftTool(BaseTool):
    name = "save_draft"
    async def execute(
            self,
            **kwargs,
    ):
        draft_id = kwargs.get("draft_id")
        user_id = kwargs.get("user_id")
        db = kwargs.get("db")
        service = GmailActionService(db=db)



        return await service.save_draft(

    draft_id=draft_id,

    user_id=user_id,

)
    
    