from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import JSON

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from backend.app.database.base import Base


class WorkflowRun(Base):

    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    workflow_name: Mapped[str]

    email_id: Mapped[int | None]

    status: Mapped[str]

    result: Mapped[dict | None] = mapped_column(
        JSON
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )