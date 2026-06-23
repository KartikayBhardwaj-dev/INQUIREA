from sqlalchemy.orm import Mapped

from sqlalchemy.orm import mapped_column
from backend.app.database.base import Base

class EmailThread(Base):
    __tablename__ = "email_threads"

    id: Mapped[int] = mapped_column(primary_key=True)

    gmail_thread_id: Mapped[str]