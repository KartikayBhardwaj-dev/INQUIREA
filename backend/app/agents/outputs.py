from pydantic import BaseModel


class AgentOutput(BaseModel):

    success: bool

    agent: str

    result: dict

    error: str | None = None