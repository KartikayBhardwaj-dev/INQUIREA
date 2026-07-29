from backend.app.tools.base_tool import BaseTool
from sqlalchemy.orm import Session

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
        service = DraftService(
            kwargs["db"],
        )

        tools = DraftTools(service)

        return {
            "status": "not_implemented",
            "message": "Save draft placeholder.",
            "draft": kwargs,
        }
    
    