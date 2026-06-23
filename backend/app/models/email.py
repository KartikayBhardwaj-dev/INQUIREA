from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy import JSON

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from backend.app.database.base import Base


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True
    )

    gmail_message_id: Mapped[str] = mapped_column(
        unique=True,
        index=True
    )

    gmail_thread_id: Mapped[str] = mapped_column(
        index=True
    )

    sender: Mapped[str]

    recipient: Mapped[str]

    subject: Mapped[str]

    snippet: Mapped[str | None]

    body: Mapped[str | None] = mapped_column(
        Text
    )

    received_at: Mapped[datetime | None]

    label_ids: Mapped[list] = mapped_column(
        JSON,
        default=list
    )

    is_processed: Mapped[bool] = mapped_column(
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )