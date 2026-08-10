from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmailIntelligenceResponse(BaseModel):
    id: int

    # Local database Email.id
    email_id: int

    # Actual Gmail API message ID
    gmail_message_id: str

    # Intelligence
    category: str | None
    priority: str | None
    summary: str | None

    extracted_data: dict | None
    tags: list | None
    confidence: float | None

    processed_at: datetime | None

    # Email metadata
    sender: str
    recipient: str
    subject: str
    snippet: str | None
    received_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )