import asyncio
from datetime import datetime

from fastapi import Request
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.database.session import SessionLocal

from backend.app.models.email import Email
from backend.app.models.email_intelligence import EmailIntelligence
from backend.app.models.workflow_run import WorkflowRun

from backend.app.workflows.workflow_service import WorkflowService

settings = get_settings()


class EmailIntelligenceService:

    @staticmethod
    async def process_email(
        db: Session,
        email: Email,
        request: Request,
    ):
        existing = (
            db.query(EmailIntelligence)
            .filter(
                EmailIntelligence.email_id == email.id
            )
            .first()
        )

        if existing:
            return existing

        # FIX: Open an explicit transaction savepoint boundary.
        # This isolates our workflow record tracking from internal agent commit commands.
        nested_transaction = db.begin_nested()

        workflow_run = WorkflowRun(
            workflow_name="email_processing",
            email_id=email.id,
            status="running",
            result={},
        )

        db.add(workflow_run)
        db.flush()  # Allocates ID safely within the nested transaction

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

            config = {
                "configurable": {
                    "db": db
                }
            }

            result = await WorkflowService.run_email_workflow(
                state=state,
                config=config,
                request=request,
            )

            # Clean db metadata fields out of tracking results dictionary safely
            if isinstance(result, dict):
                result.pop("db", None)

            intelligence = EmailIntelligence(
                email_id=email.id,
                category=result.get("category"),
                priority=result.get("priority"),
                summary=result.get("summary"),
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

            # Safely finalize workflow tracking metadata
            workflow_run.status = "completed"
            workflow_run.result = result

            # Commit the isolated tracking savepoint layer first
            nested_transaction.commit()
            
            # Commit changes to the database
            db.commit()
            db.refresh(intelligence)

            return intelligence

        except Exception as e:
            # Rollback the tracking savepoint layer safely on failure
            try:
                nested_transaction.rollback()
            except Exception:
                pass

            # Create a separate, fresh log for the failure state
            db.rollback()
            
            fail_session = SessionLocal()
            try:
                failed_run = WorkflowRun(
                    workflow_name="email_processing",
                    email_id=email.id,
                    status="failed",
                    result={"error": str(e)},
                )
                fail_session.add(failed_run)
                
                # Ensure the email status update is logged even on failure
                failed_email = fail_session.query(Email).filter(Email.id == email.id).first()
                if failed_email:
                    failed_email.is_processed = False
                
                fail_session.commit()
            except Exception as internal_err:
                print(f"Failed logging transaction state error: {internal_err}")
            finally:
                fail_session.close()

            raise

    @staticmethod
    async def process_single_email(
        email_id: int,
        semaphore: asyncio.Semaphore,
        request: Request,
    ):
        async with semaphore:
            db = SessionLocal()
            try:
                email = (
                    db.query(Email)
                    .filter(
                        Email.id == email_id
                    )
                    .first()
                )

                if email is None:
                    return False

                result = await EmailIntelligenceService.process_email(
                    db=db,
                    email=email,
                    request=request,
                )

                return result is not None

            except Exception as e:
                print(
                    f"Email {email_id} failed: {e}"
                )
                return False
            finally:
                db.close()

    @staticmethod
    async def process_all_unprocessed(
        db: Session,
        request: Request,
    ):
        email_ids = [
            email.id
            for email in (
                db.query(Email)
                .filter(
                    Email.is_processed == False
                )
                .all()
            )
        ]

        if not email_ids:
            return 0

        CHUNK_SIZE = settings.MAX_CONCURRENT_EMAILS
        processed_count = 0
        
        semaphore = asyncio.Semaphore(CHUNK_SIZE)

        for i in range(0, len(email_ids), CHUNK_SIZE):
            chunk = email_ids[i:i + CHUNK_SIZE]
            
            tasks = [
                EmailIntelligenceService.process_single_email(
                    email_id=email_id,
                    semaphore=semaphore,
                    request=request,
                )
                for email_id in chunk
            ]

            results = await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

            processed_count += sum(
                1 for result in results if result is True
            )

            if i + CHUNK_SIZE < len(email_ids):
                await asyncio.sleep(2.5)

        return processed_count