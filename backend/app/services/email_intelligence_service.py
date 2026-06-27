from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.email import Email
from backend.app.models.email_intelligence import (
    EmailIntelligence,
)

from backend.app.models.workflow_run import (
    WorkflowRun,
)

from backend.app.workflows.workflow_service import (
    WorkflowService,
)


class EmailIntelligenceService:

    @staticmethod
    async def process_email(
        db: Session,
        email: Email,
    ):

        existing = (
            db.query(
                EmailIntelligence
            )
            .filter(
                EmailIntelligence.email_id
                == email.id
            )
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
        db.commit()
        db.refresh(workflow_run)

        try:

            state = {
    "email_id": email.id,
    "subject": email.subject or "",
    "sender": email.sender or "",
    "body": email.body or "",
    "category": None,
    "priority": None,
    "summary": None,
    "draft_reply": None,
    "thread_summary": None,
    "tone": "professional",
    "thread_context": "",
    "extracted_data": {},
    "memory": {},
    "next_agent": None,
    "errors": [],
}

            result = (
                await WorkflowService
                .run_email_workflow(
                    state
                )
            )

            intelligence = EmailIntelligence(
                email_id=email.id,
                category=result.get(
                    "category"
                ),
                priority=result.get(
                    "priority"
                ),
                summary=result.get(
                    "summary"
                ),
                extracted_data=result.get(
                    "extracted_data",
                    {},
                ),
                tags=[],
                confidence=1.0,
                processed_at=datetime.utcnow(),
            )

            db.add(intelligence)

            email.is_processed = True

            workflow_run.status = (
                "completed"
            )

            workflow_run.result = (
                result
            )

            db.commit()

            db.refresh(
                intelligence
            )

            return intelligence

        except Exception as e:

            workflow_run.status = (
                "failed"
            )

            workflow_run.result = {
                "error": str(e)
            }

            db.commit()

            raise e

    @staticmethod
    async def process_all_unprocessed(
        db: Session,
    ):

        emails = (
            db.query(Email)
            .filter(
                Email.is_processed
                == False
            )
            .all()
        )

        processed = 0

        for email in emails:

            try:

                result = (
                    await EmailIntelligenceService
                    .process_email(
                        db,
                        email,
                    )
                )

                if result:
                    processed += 1

            except Exception as e:

                print(
                    f"Email {email.id} failed: {e}"
                )

        return processed