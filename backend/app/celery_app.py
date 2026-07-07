from celery import Celery
from celery.signals import worker_process_init

from backend.app.core.config import get_settings
from backend.app.tools.bootstrap import register_tools
from backend.app.agents.bootstrap import register_agents

settings = get_settings()

celery_app = Celery(
    "inquirea",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    timezone="UTC",
    enable_utc=True,

    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,

    result_expires=3600,

    include=[
        "backend.app.tasks.email_tasks",
        "backend.app.tasks.embedding_tasks",
    ],

    beat_schedule={},
)

celery_app.set_default()

celery_app.autodiscover_tasks(
    [
        "backend.app.tasks",
    ]
)


@worker_process_init.connect
def initialize_worker(**kwargs):
    """
    Runs once in every Celery worker process.
    """
    register_tools()
    register_agents()

    print("✓ Celery worker initialized")