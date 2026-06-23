from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from backend.app.database.base import Base


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    gmail_id: Mapped[str]

    thread_id: Mapped[str]

    sender: Mapped[str]

    subject: Mapped[str]

    body: Mapped[str] = mapped_column(
        Text
    )

    received_at: Mapped[datetime | None]

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )