from __future__ import annotations

import logging
from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.app.services.email_tool_service import EmailToolService
from backend.app.tools.base_tool import BaseTool
from backend.app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Argument Schemas for Tool Validation
# =============================================================================

class SearchEmailsInput(BaseModel):
    query: str = Field(..., description="Semantic or keyword search query for retrieving emails.")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum number of emails to retrieve.")
    category: Optional[str] = Field(default=None, description="Optional email category filter (e.g., Work, Personal, Marketing).")
    priority: Optional[str] = Field(default=None, description="Optional priority level (e.g., High, Medium, Low).")
    sender: Optional[str] = Field(default=None, description="Filter emails received from a specific sender email address or domain.")
    requires_reply: Optional[bool] = Field(default=None, description="Filter for emails that explicitly require or do not require a reply.")
    sort_by: str = Field(default="relevance", description="Sorting strategy: 'relevance' or 'date'.")
    date_from: Optional[str] = Field(default=None, description="Filter emails received on or after ISO date (YYYY-MM-DD).")
    date_to: Optional[str] = Field(default=None, description="Filter emails received on or before ISO date (YYYY-MM-DD).")


class GetEmailInput(BaseModel):
    email_id: int = Field(..., description="The unique integer ID of the email to retrieve.")


class SummarizeThreadInput(BaseModel):
    email_ids: list[int] = Field(..., min_length=1, description="List of unique email IDs belonging to the thread to summarize.")


class ListReplyRequiredInput(BaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of actionable emails requiring replies to retrieve.")


# =============================================================================
# Main EmailTools Class & BaseTool Concrete Wrappers
# =============================================================================

class EmailTools:
    """
    Thin wrapper around EmailToolService.

    Responsibilities
    ----------------
    - Expose reusable email operations for Level 2 LLM tool execution.
    - Validate tool arguments via Pydantic schemas.
    - Delegate all business logic strictly to EmailToolService.
    - Contain NO direct SQL queries, repository access, or raw LLM prompts.
    """

    def __init__(self, service: EmailToolService):
        self.service = service

    def search_emails(
        self,
        query: str,
        limit: int = 5,
        category: str | None = None,
        priority: str | None = None,
        sender: str | None = None,
        requires_reply: bool | None = None,
        sort_by: str = "relevance",
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search emails using semantic hybrid retrieval."""
        return self.service.search_emails(
            query=query,
            limit=limit,
            category=category,
            priority=priority,
            sender=sender,
            requires_reply=requires_reply,
            sort_by=sort_by,
            date_from=date_from,
            date_to=date_to,
        )

    def get_email(self, email_id: int) -> dict[str, Any] | None:
        """Retrieve a single email by ID."""
        return self.service.get_email(email_id)

    def summarize_thread(self, email_ids: list[int]) -> list[dict[str, Any]]:
        """Retrieve multiple emails for thread summarization."""
        return self.service.summarize_thread(email_ids)

    def list_reply_required(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return emails that require replies."""
        return self.service.list_reply_required(limit=limit)


# =============================================================================
# Level 2 Tool Registration Helpers
# =============================================================================

class SearchEmailsTool(BaseTool):
    name = "search_emails"
    description = "Search inbox history using semantic queries, date ranges, senders, or priority filters."
    args_schema = SearchEmailsInput

    def __init__(self, email_tools: EmailTools):
        self.tools = email_tools

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        params = SearchEmailsInput(**kwargs).model_dump()
        results = self.tools.search_emails(**params)
        return {
            "message": f"Successfully retrieved {len(results)} email(s).",
            "emails_found": len(results),
            "retrieved_emails": results,
        }


class GetEmailTool(BaseTool):
    name = "get_email"
    description = "Retrieve detailed metadata and body content for a specific email using its email_id."
    args_schema = GetEmailInput

    def __init__(self, email_tools: EmailTools):
        self.tools = email_tools

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        params = GetEmailInput(**kwargs).model_dump()
        email = self.tools.get_email(params["email_id"])
        if not email:
            return {
                "message": f"Email with ID {params['email_id']} was not found.",
                "emails_found": 0,
                "retrieved_emails": [],
            }
        return {
            "message": f"Successfully loaded email ID {params['email_id']}.",
            "emails_found": 1,
            "retrieved_emails": [email],
        }


class ListReplyRequiredTool(BaseTool):
    name = "list_reply_required"
    description = "List all unhandled inbox emails that explicitly require user action or a reply."
    args_schema = ListReplyRequiredInput

    def __init__(self, email_tools: EmailTools):
        self.tools = email_tools

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        params = ListReplyRequiredInput(**kwargs).model_dump()
        results = self.tools.list_reply_required(limit=params["limit"])
        return {
            "message": f"Found {len(results)} email(s) requiring a reply.",
            "emails_found": len(results),
            "retrieved_emails": results,
        }


def register_email_tools(service: EmailToolService) -> EmailTools:
    """
    Factory function to instantiate EmailTools and register all
    corresponding BaseTool instances into the global ToolRegistry.
    """
    tools_instance = EmailTools(service)
    
    ToolRegistry.register(SearchEmailsTool(tools_instance))
    ToolRegistry.register(GetEmailTool(tools_instance))
    ToolRegistry.register(ListReplyRequiredTool(tools_instance))
    
    logger.info("Successfully registered EmailTools with ToolRegistry.")
    return tools_instance