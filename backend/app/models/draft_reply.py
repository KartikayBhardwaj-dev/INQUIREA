from sqlalchemy.orm import Mapped

from sqlalchemy.orm import mapped_column
from backend.app.database.base import Base

class DraftReply(Base):
    __tablename__ = "draft_replies"

    id: Mapped[int] = mapped_column(primary_key=True)

    email_id: Mapped[int]

    draft: Mapped[str]