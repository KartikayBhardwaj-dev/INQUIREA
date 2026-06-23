from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from backend.app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True
    )

    full_name: Mapped[str | None]

    google_id: Mapped[str | None]

    profile_picture: Mapped[str | None]

    google_access_token: Mapped[str | None]

    google_refresh_token: Mapped[str | None]

    last_sync_at: Mapped[datetime | None]

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )