import logging

from backend.app.database.session import SessionLocal
from backend.app.services.vector_memory_service import (
    VectorMemoryService,
)

logger = logging.getLogger(__name__)


class EmbeddingWorker:
    """
    Executes embedding jobs.

    Owns the database session because it runs
    inside a Celery worker.
    """

    @staticmethod
    def process_embedding(email_id: int) -> None:

        db = SessionLocal()

        try:
            VectorMemoryService.add_email(
                db=db,
                email_id=email_id,
            )

            logger.info(
                "Indexed email %s",
                email_id,
            )

        except Exception:
            logger.exception(
                "Failed to index email %s",
                email_id,
            )
            raise

        finally:
            db.close()

    @staticmethod
    def process_embedding_batch(
        email_ids: list[int],
    ) -> None:

        if not email_ids:
            return

        db = SessionLocal()

        try:
            VectorMemoryService.add_batch(
                db=db,
                email_ids=email_ids,
            )

            logger.info(
                "Indexed %s emails",
                len(email_ids),
            )

        except Exception:
            logger.exception(
                "Failed batch indexing (%s emails)",
                len(email_ids),
            )
            raise

        finally:
            db.close()