from typing import Any, TypedDict


class WorkflowState(TypedDict):

    email_id: int

    subject: str

    sender: str

    body: str

    category: str | None

    priority: str | None

    summary: str | None

    thread_summary: str | None

    extracted_data: dict[str, Any]

    memory: dict[str, Any]

    thread_context: str | None

    errors: list[str]