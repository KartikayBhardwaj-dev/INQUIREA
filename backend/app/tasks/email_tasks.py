import logging
from backend.app.celery_app import celery_app
from backend.app.database.session import SessionLocal
from backend.app.models.email import Email
from backend.app.services.email_intelligence_service import (
    EmailIntelligenceService,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_email(self, email_id: int):
    """
    Process a single email in the background queue.
    """
    db = SessionLocal()

    try:
        email = db.query(Email).filter(Email.id == email_id).first()

        if email is None:
            logger.warning("Email ID %s not found for background processing.", email_id)
            return

        EmailIntelligenceService.process_email_sync(
            db=db,
            email=email,
        )
    except Exception as exc:
        db.rollback()
        logger.exception("Error processing email ID %s in worker task.", email_id)
        raise exc
    finally:
        db.close()


@celery_app.task
def process_email_batch(email_ids: list[int]):
    """
    Process multiple emails by fanning out worker tasks.
    """
    for email_id in email_ids:
        process_email.delay(email_id)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def retry_failed_email(self, email_id: int):
    """
    Retry a failed email processing task.
    """
    process_email.delay(email_id)