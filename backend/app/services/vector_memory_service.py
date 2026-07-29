from __future__ import annotations

import logging
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.models.email import Email
from backend.app.models.email_intelligence import EmailIntelligence
from backend.app.repositories.email_embedding_repository import (
    EmailEmbeddingRepository,
)

logger = logging.getLogger(__name__)


class VectorMemoryService:
    """
    Business layer for semantic email memory.
    """

    @staticmethod
    def _build_document(
        email: Email,
        intelligence: EmailIntelligence | None,
    ) -> str:
        summary = ""
        category = ""
        priority = ""
        requires_reply = False
        organizations: list[str] = []
        people: list[str] = []
        dates: list[str] = []
        action_items: list[str] = []

        if intelligence:
            summary = intelligence.summary or ""
            category = intelligence.category or ""
            priority = intelligence.priority or ""
            extracted = intelligence.extracted_data or {}

            requires_reply = extracted.get("requires_reply", False)
            entities = extracted.get("extracted_entities", {})

            organizations = entities.get("organizations", [])
            people = entities.get("people", [])
            dates = entities.get("dates", [])
            action_items = entities.get("action_items", [])

        return f"""
Subject:
{email.subject or ""}

Summary:
{summary}

Category:
{category}

Priority:
{priority}

Requires Reply:
{requires_reply}

Organizations:
{", ".join(organizations)}

People:
{", ".join(people)}

Dates:
{", ".join(dates)}

Action Items:
{", ".join(action_items)}

Sender:
{email.sender or ""}

Recipient:
{email.recipient or ""}

Email Body:
{email.body or ""}
""".strip()

    @staticmethod
    def _build_metadata(
        email: Email,
        intelligence: EmailIntelligence | None,
    ) -> dict:
        category = None
        priority = None
        requires_reply = False
        organizations: list[str] = []
        people: list[str] = []

        if intelligence:
            category = intelligence.category
            priority = intelligence.priority
            extracted = intelligence.extracted_data or {}
            requires_reply = extracted.get("requires_reply", False)
            entities = extracted.get("extracted_entities", {})
            organizations = entities.get("organizations", [])
            people = entities.get("people", [])

        return {
            "email_id": email.id,
            "user_id": getattr(email, "user_id", None),
            "thread_id": email.gmail_thread_id,
            "sender": email.sender,
            "recipient": email.recipient,
            "subject": email.subject,
            "category": category,
            "priority": priority,
            "requires_reply": requires_reply,
            "organizations": organizations,
            "people": people,
            "received_at": email.received_at.isoformat() if email.received_at else None,
        }

    @classmethod
    def build_batch(
        cls,
        db: Session,
        email_ids: list[int],
    ) -> list[dict]:
        if not email_ids:
            return []

        emails = db.query(Email).filter(Email.id.in_(email_ids)).all()
        email_lookup = {email.id: email for email in emails}

        intelligence_rows = (
            db.query(EmailIntelligence)
            .filter(EmailIntelligence.email_id.in_(email_ids))
            .all()
        )
        intelligence_lookup = {row.email_id: row for row in intelligence_rows}

        items: list[dict] = []
        for email_id in email_ids:
            email = email_lookup.get(email_id)
            if email is None:
                continue

            intelligence = intelligence_lookup.get(email_id)
            document = cls._build_document(email, intelligence)
            if not document.strip():
                continue

            items.append(
                {
                    "email_id": email.id,
                    "document": document,
                    "metadata": cls._build_metadata(email, intelligence),
                }
            )

        return items

    @classmethod
    def index_email(cls, db: Session, email_id: int) -> int:
        return cls.index_batch(db=db, email_ids=[email_id])

    @classmethod
    def index_batch(cls, db: Session, email_ids: list[int]) -> int:
        items = cls.build_batch(db=db, email_ids=email_ids)
        if not items:
            logger.info("No emails available for embedding.")
            return 0

        repository = EmailEmbeddingRepository(db)
        try:
            repository.upsert_many(items=items)
            db.commit()
        except Exception:
            db.rollback()
            raise

        logger.info("Indexed %s email(s) into pgvector.", len(items))
        return len(items)

    @classmethod
    def update_email(cls, db: Session, email_id: int) -> int:
        return cls.index_email(db=db, email_id=email_id)

    @classmethod
    def delete_email(cls, db: Session, email_id: int) -> None:
        repository = EmailEmbeddingRepository(db)
        try:
            repository.delete(email_id=email_id)
            db.commit()
        except Exception:
            db.rollback()
            raise

        logger.info("Deleted embedding for email %s.", email_id)

    @classmethod
    def similarity_search(
        cls,
        db: Session,
        query: str,
        limit: int = 5,
        user_id: Optional[int] = None,
    ) -> list[Email]:
        repository = EmailEmbeddingRepository(db)
        matches = repository.similarity_search(query=query, limit=limit, user_id=user_id)
        logger.debug("Semantic search returned %s emails.", len(matches))
        return matches

    @classmethod
    def reindex_all(cls, db: Session) -> int:
        repository = EmailEmbeddingRepository(db)
        logger.info("Starting full pgvector reindex.")

        try:
            repository.reset()
            db.commit()
        except Exception:
            db.rollback()
            raise

        emails = db.query(Email).order_by(Email.id.asc()).all()
        if not emails:
            logger.info("No emails found for reindex.")
            return 0

        email_ids = [email.id for email in emails]
        indexed = cls.index_batch(db=db, email_ids=email_ids)
        logger.info("Finished pgvector reindex (%s emails).", indexed)
        return indexed