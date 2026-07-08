from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from backend.app.database.base import Base


class ChatHistory(Base):
    """
    Stores AI Inbox Chat conversation history.

    Each row represents a single message exchanged
    between the user and the assistant.

    Used for:
    - conversation persistence
    - follow-up questions
    - conversation memory
    """

    __tablename__ = "chat_history"

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="ck_chat_history_role",
        ),
    )

    # ---------------------------------------------------------
    # Primary Key
    # ---------------------------------------------------------

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    # ---------------------------------------------------------
    # Conversation
    # ---------------------------------------------------------

    conversation_id: Mapped[str] = mapped_column(
        String(64),
        default=lambda: str(uuid4()),
        index=True,
        nullable=False,
    )

    # ---------------------------------------------------------
    # User
    # ---------------------------------------------------------

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    # ---------------------------------------------------------
    # Message
    # ---------------------------------------------------------

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    # Allowed values:
    # - user
    # - assistant
    # - system

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ---------------------------------------------------------
    # Timestamp
    # ---------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
        nullable=False,
    )