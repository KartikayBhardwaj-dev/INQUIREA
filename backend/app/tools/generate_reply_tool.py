from sqlalchemy.orm import Session

from backend.app.services.draft_service import DraftService
from backend.app.tools.base_tool import BaseTool
from backend.app.tools.draft_tools import DraftTools

from backend.app.services.gmail_action_service import GmailActionService
# class GenerateReplyTool(BaseTool):

#     name = "generate_reply"

#     async def execute(
#         self,
#         db: Session,
#         **kwargs,
#     ):
#         tools = DraftTools(
#             DraftService(db),
#         )

#         email_id = kwargs.get("email_id")

#         if email_id is None:
#             raise ValueError("email_id is required.")

#         draft = await tools.generate_reply(
#             email_id=email_id,
#             tone=kwargs.get(
#                 "tone",
#                 "professional",
#             ),
#         )

#         return {
#             "draft_id": draft.id,
#             "email_id": draft.email_id,
#             "draft": draft.draft,
#             "version": draft.version,
#             "tone": draft.tone,
#             "is_current": draft.is_current,
#         }


class GenerateReplyTool(BaseTool):

    name = "generate_reply"

    async def execute(
        self,
        **kwargs,
    ):
        service = DraftService(
            kwargs["db"],
        )

        tools = DraftTools(service)

        draft = await tools.generate_reply(
            email_id=kwargs["email_id"],
            tone=kwargs.get(
                "tone",
                "professional",

            ),
            user_id=kwargs["user_id"]
        )

        gmail_service = GmailActionService(

    db=kwargs["db"]

)

        gmail_result = await gmail_service.save_draft(

    draft_id=draft.id,

    user_id=kwargs["user_id"]

)

        return {

    "draft_id": draft.id,

    "email_id": draft.email_id,

    "draft": draft.draft,

    "version": draft.version,

    "tone": draft.tone,

    "is_current": draft.is_current,

    "gmail_draft_id": gmail_result.get("gmail_draft_id"),

}