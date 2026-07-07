import asyncio
import logging

from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.database.session import SessionLocal
from backend.app.models.email import Email
from backend.app.services.email_queue import EmailQueue

logger = logging.getLogger(__name__)

settings = get_settings()


class EmailScheduler:
    """
    Periodically scans the database for unprocessed emails
    and pushes them into the EmailQueue.
    """

    def __init__(self, worker_pool):
        self.worker_pool = worker_pool
        self._queued_email_ids: set[int] = set()

    async def enqueue_unprocessed(
        self,
        db: Session,
    ) -> int:

        emails = (
            db.query(Email)
            .filter(
                Email.is_processed.is_(False)
            )
            .order_by(Email.id)
            .all()
        )

        count = 0

        for email in emails:

            if email.id in self._queued_email_ids:
                continue

            await EmailQueue.put(email.id)

            self._queued_email_ids.add(email.id)

            count += 1

        if count:
            logger.info(
                "Enqueued %s email(s).",
                count,
            )

        return count

    async def run(self):
        """
        Continuously watches for new unprocessed emails.
        """

        logger.info("Email Scheduler started.")

        while True:

            db = SessionLocal()

            try:

                await self.enqueue_unprocessed(db)

                processed = (
                    db.query(Email.id)
                    .filter(
                        Email.is_processed.is_(True)
                    )
                    .all()
                )

                for (email_id,) in processed:
                    self._queued_email_ids.discard(email_id)

            except Exception:

                logger.exception(
                    "Email Scheduler failed."
                )

            finally:

                db.close()

            await asyncio.sleep(
                settings.QUEUE_POLL_INTERVAL
            )

    async def wait_until_finished(self):
        """
        Wait until the email queue is empty.
        """

        await EmailQueue.join()