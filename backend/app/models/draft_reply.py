from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class DraftReply(Base):
    __tablename__ = "draft_replies"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    email_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("emails.id"),
        index=True,
        nullable=False,
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    draft: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    tone: Mapped[str] = mapped_column(
        String(50),
        default="professional",
        nullable=False,
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ---------------------------------------------------------
    # Gmail Sync
    # ---------------------------------------------------------

    gmail_draft_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Timestamps
    # ---------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    approval: Mapped["Approval"] = relationship(
        "Approval",
        back_populates="draft_reply",
        uselist=False,
        cascade="all, delete-orphan",
    )