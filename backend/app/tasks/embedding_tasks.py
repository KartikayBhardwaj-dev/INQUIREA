from backend.app.celery_app import celery_app

from backend.app.services.embedding_worker import (
    EmbeddingWorker,
)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def generate_embedding(
    self,
    email_id: int,
):
    """
    Generate embedding for one email.
    """

    EmbeddingWorker.process_embedding(
        email_id=email_id,
    )


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def generate_embedding_batch(
    self,
    email_ids: list[int],
):
    """
    Generate embeddings for many emails.
    """

    EmbeddingWorker.process_embedding_batch(
        email_ids=email_ids,
    )