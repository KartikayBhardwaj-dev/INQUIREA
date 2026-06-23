
from sqlalchemy.orm import Mapped

from sqlalchemy.orm import mapped_column
from backend.app.database.base import Base
class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    workflow_name: Mapped[str]