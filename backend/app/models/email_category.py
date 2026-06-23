from sqlalchemy.orm import Mapped

from sqlalchemy.orm import mapped_column
from backend.app.database.base import Base

class EmailCategory(Base):
    __tablename__ = "email_categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    email_id: Mapped[int]

    category: Mapped[str]