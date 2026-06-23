from datetime import datetime

from pydantic import BaseModel


class EmailIntelligenceResponse(
    BaseModel
):
    id: int

    email_id: int

    category: str | None

    priority: str | None

    summary: str | None

    extracted_data: dict | None

    tags: list | None

    confidence: float | None

    processed_at: datetime | None

    class Config:
        from_attributes = True