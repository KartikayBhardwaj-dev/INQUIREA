from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class ChatRequest(BaseModel):
    """
    Incoming user chat request.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )

    conversation_id: str | None = None


class ChatMessage(BaseModel):
    """
    Single chat message.
    """

    role: str

    content: str

    created_at: datetime


class ConversationHistory(BaseModel):
    """
    Full conversation history.
    """

    conversation_id: str

    messages: list[ChatMessage]


class RetrievedEmail(BaseModel):
    """
    Email citation returned by the AI.
    """

    email_id: int

    subject: str

    sender: str

    category: str | None = None

    priority: str | None = None

    received_at: datetime | None = None


class ChatResponse(BaseModel):
    """
    Response returned from the AI Inbox Chat.
    """

    conversation_id: str

    answer: str

    sources: list[int] = []

    emails_found: int = 0

    retrieved_emails: list[RetrievedEmail] = []

    query_plan: dict[str, Any] | None = None