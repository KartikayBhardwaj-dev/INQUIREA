from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from backend.app.agents.registry import AgentRegistry
from backend.app.database.session import SessionLocal
from backend.app.models.email import Email
from backend.app.models.email_intelligence import EmailIntelligence
from backend.app.models.workflow_run import WorkflowRun
from backend.app.services.vector_memory_service import VectorMemoryService

logger = logging.getLogger(__name__)


class EmailIntelligenceService:
    """
    Business logic for generating email intelligence.
    API endpoints enqueue Celery jobs. Workers execute process_email_sync().
    """

    @staticmethod
    async def process_email(
        db: Session,
        email: Email,
    ) -> EmailIntelligence:
        return await EmailIntelligenceService._process(
            db=db,
            email=email,
        )

    @staticmethod
    def process_email_sync(
        db: Session,
        email: Email,
    ) -> EmailIntelligence:
        """
        Synchronous wrapper for Celery workers.
        Handles event loop execution cleanly.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # In case worker is already running inside an existing loop
            future = asyncio.run_coroutine_threadsafe(
                EmailIntelligenceService._process(db=db, email=email),
                loop,
            )
            return future.result()
        else:
            return loop.run_until_complete(
                EmailIntelligenceService._process(db=db, email=email)
            )

    @staticmethod
    async def _process(
        db: Session,
        email: Email,
    ) -> EmailIntelligence:

        existing = (
            db.query(EmailIntelligence)
            .filter(EmailIntelligence.email_id == email.id)
            .first()
        )

        if existing:
            return existing

        workflow_run = WorkflowRun(
            workflow_name="email_processing",
            email_id=email.id,
            status="running",
            result={},
        )

        db.add(workflow_run)

        try:
            state = {
                "email_id": email.id,
                "subject": email.subject or "",
                "sender": email.sender or "",
                "body": email.body or "",
                "thread_context": "",
                "category": None,
                "priority": None,
                "summary": None,
                "requires_reply": False,
                "extracted_entities": {},
                "errors": [],
            }

            analysis_agent = AgentRegistry.get("analysis_agent")
            result = await analysis_agent.run(state)

            if not result.get("success", False):
                raise RuntimeError(result.get("error", "Analysis agent execution failed."))

            output = result.get("result", {})

            intelligence = EmailIntelligence(
                email_id=email.id,
                category=output.get("category"),
                priority=output.get("priority"),
                summary=output.get("summary"),
                extracted_data={
                    "requires_reply": output.get("requires_reply", False),
                    "extracted_entities": output.get("extracted_entities", {}),
                },
                tags=[],
                confidence=1.0,
                processed_at=datetime.utcnow(),
            )

            db.add(intelligence)
            email.is_processed = True

            workflow_run.status = "completed"
            workflow_output = dict(output)
            workflow_output.pop("db", None)
            workflow_run.result = workflow_output

            db.commit()

            # Execute vector embedding indexing in an isolated try-except block
            try:
                VectorMemoryService.index_email(
                    db=db,
                    email_id=email.id,
                )
            except Exception:
                logger.exception("Failed creating embedding for email %s", email.id)

            return intelligence

        except Exception as e:
            db.rollback()
            logger.exception("Failed processing email ID %s", email.id)

            fail_session = SessionLocal()
            try:
                failed_run = WorkflowRun(
                    workflow_name="email_processing",
                    email_id=email.id,
                    status="failed",
                    result={"error": str(e)},
                )
                fail_session.add(failed_run)

                failed_email = (
                    fail_session.query(Email)
                    .filter(Email.id == email.id)
                    .first()
                )

                if failed_email:
                    failed_email.is_processed = False

                fail_session.commit()
            finally:
                fail_session.close()

            raise