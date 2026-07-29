# from backend.app.tools.base_tool import BaseTool
# from sqlalchemy.orm import Session

# from backend.app.services.draft_service import DraftService
# from backend.app.tools.draft_tools import DraftTools
# class RewriteReplyTool(BaseTool):

#     name = "rewrite_reply"

#     async def execute(self,db: Session, **kwargs):
#         tools = DraftTools(
#             DraftService(db),
#         )
#         return {
#             "status": "not_implemented",
#             "message": "Rewrite reply placeholder.",
#             "tone": kwargs.get("tone"),
#         }


from __future__ import annotations

from backend.app.services.draft_service import DraftService
from backend.app.tools.base_tool import BaseTool
from backend.app.tools.draft_tools import DraftTools


class RewriteReplyTool(BaseTool):

    name = "rewrite_reply"

    async def execute(
        self,
        **kwargs,
    ):
        service = DraftService(
            kwargs["db"],
        )

        tools = DraftTools(
            service,
        )

        draft = await tools.rewrite_reply(
            draft_id=kwargs["draft_id"],
            tone=kwargs.get(
                "tone",
                "professional",
            ),
        )

        return {
            "draft_id": draft.id,
            "email_id": draft.email_id,
            "draft": draft.draft,
            "version": draft.version,
            "tone": draft.tone,
            "is_current": draft.is_current,
        }