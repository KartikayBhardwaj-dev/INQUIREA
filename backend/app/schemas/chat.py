from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ChatRequest(BaseModel):
    """
    Incoming AI Inbox Chat request.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User's inbox question.",
    )

    conversation_id: str | None = Field(
        default=None,
        description="Existing conversation ID for follow-up questions.",
    )


class ChatMessage(BaseModel):
    """
    One conversation message.
    """

    model_config = ConfigDict(from_attributes=True)

    role: str

    content: str

    created_at: datetime


class ConversationHistory(BaseModel):
    """
    Complete conversation history.
    """

    conversation_id: str

    messages: list[ChatMessage]


class RetrievedEmail(BaseModel):
    """
    Email metadata returned by the AI retrieval pipeline.

    Important:
    - email_id = local database email ID
    - gmail_message_id = actual Gmail message ID
    """

    email_id: int

    gmail_message_id: str | None = None

    subject: str

    sender: str

    recipient: str | None = None

    category: str | None = None

    priority: str | None = None

    received_at: datetime | None = None

    summary: str | None = None

    requires_reply: bool = False

    entities: dict[str, Any] = Field(
        default_factory=dict
    )

    action_items: list[Any] = Field(
        default_factory=list
    )


class ChatResponse(BaseModel):
    """
    Standard AI Inbox Chat response.

    Every chatbot response uses this same structure.

    Normal retrieval response:

    {
        "conversation_id": "...",
        "answer": "...",
        "sources": [],
        "emails_found": 2,
        "retrieved_emails": [],
        "query_plan": {},
        "tool": null,
        "tool_result": null
    }

    Tool response:

    {
        "conversation_id": "...",
        "answer": "Draft generated successfully.",
        "sources": [],
        "emails_found": 0,
        "retrieved_emails": [],
        "query_plan": {},
        "tool": "generate_reply",
        "tool_result": {
            "status": "success",
            "success": true,
            "tool_name": "generate_reply",
            "result": {
                "draft_id": 12,
                "email_id": 45,
                "draft": "Hi Google Team...",
                "version": 1,
                "tone": "professional",
                "approval_status": "pending",
                "gmail_draft_id": "abc123",
                "is_sent": false
            },
            "error": null
        }
    }
    """

    conversation_id: str
    answer: str

    sources: list[int] = Field(default_factory=list)

    emails_found: int = Field(
        default=0,
        ge=0,
    )

    retrieved_emails: list[RetrievedEmail] = Field(
        default_factory=list,
    )

    query_plan: dict[str, Any] = Field(
        default_factory=dict,
    )

    tool: str | None = Field(
        default=None,
    )

    tool_result: dict[str, Any] | None = Field(
        default=None,
    )
    error: dict[str, Any] | None = Field(
    default=None,
    description="Structured error returned when an action fails.",
)