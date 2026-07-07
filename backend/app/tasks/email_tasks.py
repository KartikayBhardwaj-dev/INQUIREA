from backend.app.celery_app import celery_app

from backend.app.database.session import SessionLocal
from backend.app.models.email import Email
from backend.app.services.email_intelligence_service import (
    EmailIntelligenceService,
)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_email(
    self,
    email_id: int,
):
    """
    Process a single email.
    """

    db = SessionLocal()

    try:

        email = (
            db.query(Email)
            .filter(Email.id == email_id)
            .first()
        )

        if email is None:
            return

        EmailIntelligenceService.process_email_sync(
            db=db,
            email=email,
        )

    finally:
        db.close()


@celery_app.task
def process_email_batch(
    email_ids: list[int],
):
    """
    Process multiple emails.
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
def retry_failed_email(
    self,
    email_id: int,
):
    """
    Retry a failed email.
    """

    process_email.delay(email_id)