from datetime import datetime

from sqlalchemy import JSON
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from backend.app.database.base import Base


class EmailIntelligence(Base):
    __tablename__ = "email_intelligence"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    email_id: Mapped[int] = mapped_column(
        ForeignKey("emails.id"),
        unique=True,
        index=True
    )

    category: Mapped[str | None]

    priority: Mapped[str | None]

    summary: Mapped[str | None] = mapped_column(
        Text
    )

    extracted_data: Mapped[dict | None] = mapped_column(
        JSON
    )

    tags: Mapped[list | None] = mapped_column(
        JSON,
        default=list
    )

    confidence: Mapped[float | None]

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )