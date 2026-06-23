from sqlalchemy import ForeignKey

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from backend.app.database.base import Base


class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    email_id: Mapped[int] = mapped_column(
        ForeignKey("emails.id"),
        index=True
    )

    filename: Mapped[str]

    mime_type: Mapped[str]

    attachment_id: Mapped[str]