from pydantic import BaseModel, Field
from typing import Any


class AgentState(BaseModel):

    email_id: int | None = None

    subject: str = ""

    sender: str = ""

    body: str = ""

    category: str | None = None

    priority: str | None = None

    summary: str | None = None

    extracted_data: dict[str, Any] = Field(
        default_factory=dict
    )

    draft_reply: str | None = None

    memory: dict[str, Any] = Field(
        default_factory=dict
    )

    errors: list[str] = Field(
        default_factory=list
    )
    thread_summary: str | None