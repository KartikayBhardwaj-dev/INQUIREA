from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.services.email_tool_service import EmailToolService
from backend.app.tools.base_tool import BaseTool
from backend.app.tools.email_tools import EmailTools


class SearchEmailTool(BaseTool):

    name = "search_emails"

    async def execute(
        self,
        **kwargs,
    ):
        service = EmailToolService(
            kwargs["db"],
        )

        tools = EmailTools(service)

        return tools.search_emails(
            query=kwargs.get("query", ""),
            limit=kwargs.get("limit", 5),
            category=kwargs.get("category"),
            priority=kwargs.get("priority"),
            sender=kwargs.get("sender"),
            requires_reply=kwargs.get("requires_reply"),
            sort_by=kwargs.get("sort_by", "relevance"),
            date_from=kwargs.get("date_from"),
            date_to=kwargs.get("date_to"),
        )