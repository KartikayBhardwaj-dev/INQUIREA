from typing import Any
from typing import TypedDict


class WorkflowState(TypedDict):

    email_id: int

    subject: str

    sender: str

    body: str

    category: str | None

    priority: str | None

    summary: str | None

    extracted_data: dict[str, Any]

    memory: dict[str, Any]

    next_agent: str | None

    errors: list[str]
    thread_summary: str | None
    draft_reply: str | None

    tone: str | None

    thread_context: str | None