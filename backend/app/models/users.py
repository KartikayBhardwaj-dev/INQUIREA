from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from backend.app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    email: Mapped[str]

    full_name: Mapped[str | None]

    google_id: Mapped[str | None]

    profile_picture: Mapped[str | None]

    google_access_token: Mapped[str | None]

    google_refresh_token: Mapped[str | None]

    google_token_expiry: Mapped[datetime | None]

    last_login_at: Mapped[datetime | None]

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )