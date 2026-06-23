from sqlalchemy.orm import Mapped

from sqlalchemy.orm import mapped_column
from backend.app.database.base import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int]

    question: Mapped[str]

    answer: Mapped[str]