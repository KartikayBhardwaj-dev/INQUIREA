from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.base import Base


class EmailEmbedding(Base):
    """
    Semantic embedding for an email.
    PostgreSQL + pgvector is the source of truth.
    One email -> One embedding record.
    """

    __tablename__ = "email_embeddings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    email_id: Mapped[int] = mapped_column(
        ForeignKey(
            "emails.id",
            ondelete="CASCADE",
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    # Adjustable vector dimensions (defaults to 1536 for standard embeddings)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=False,
    )

    document: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )

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