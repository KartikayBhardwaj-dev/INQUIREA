from pydantic import BaseModel
from typing import Any


class AgentState(BaseModel):

    email_id: int | None = None

    subject: str = ""

    sender: str = ""

    body: str = ""

    intelligence: dict[str, Any] = {}

    memory: dict[str, Any] = {}

    errors: list[str] = []