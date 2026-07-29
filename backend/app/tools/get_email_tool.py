from __future__ import annotations

from backend.app.services.email_tool_service import EmailToolService
from backend.app.tools.base_tool import BaseTool


# class GetEmailTool(BaseTool):
#     """
#     Returns a single email with its intelligence.

#     Thin wrapper around EmailToolService.
#     """

#     name = "get_email"

#     async def execute(self, **kwargs):
#         service = EmailToolService(kwargs["db"])

#         return service.get_email(
#             email_id=kwargs["email_id"],
#         )



class GetEmailTool(BaseTool):
    name = "get_emails"

    async def execute(
        self,
        **kwargs,
    ):
        service = EmailToolService(
            kwargs["db"],
        )


        return service.get_emails(
            email_id=kwargs["email_id"]
        )

