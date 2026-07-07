import logging

from sqlalchemy.orm import Session

from backend.app.memory.vector_store import vector_store
from backend.app.models.email import Email
from backend.app.models.email_intelligence import EmailIntelligence

logger = logging.getLogger(__name__)


class VectorMemoryService:
    """
    Business layer for semantic email memory.

    PostgreSQL = Source of Truth
    ChromaDB = Semantic Index

    Documents are built from the persisted EmailIntelligence
    generated during the simplified ingestion pipeline.
    """

    @staticmethod
    def _build_document(
        email: Email,
        intelligence: EmailIntelligence | None,
    ) -> str:
        """
        Build the semantic document stored in Chroma.
        """

        entities = []
        reply_required = False

        if intelligence and intelligence.extracted_data:

            entities = intelligence.extracted_data.get(
                "entities",
                [],
            )

            reply_required = intelligence.extracted_data.get(
                "reply_required",
                False,
            )

        return f"""
Subject:
{email.subject or ""}

Summary:
{intelligence.summary if intelligence else ""}

Category:
{intelligence.category if intelligence else ""}

Priority:
{intelligence.priority if intelligence else ""}

Reply Required:
{reply_required}

Entities:
{", ".join(entities)}

Email Body:
{email.body or ""}
""".strip()

    @staticmethod
    def _build_metadata(
        email: Email,
        intelligence: EmailIntelligence | None,
    ) -> dict:
        """
        Metadata stored alongside the vector.
        """

        reply_required = False

        if intelligence and intelligence.extracted_data:
            reply_required = intelligence.extracted_data.get(
                "reply_required",
                False,
            )

        return {
            "email_id": email.id,
            "thread_id": email.gmail_thread_id,
            "user_id": email.user_id,
            "sender": email.sender,
            "recipient": email.recipient,
            "date": (
                email.received_at.isoformat()
                if email.received_at
                else None
            ),
            "category": (
                intelligence.category
                if intelligence
                else None
            ),
            "priority": (
                intelligence.priority
                if intelligence
                else None
            ),
            "reply_required": reply_required,
        }

    @classmethod
    def build_batch(
        cls,
        db: Session,
        email_ids: list[int],
    ) -> list[dict]:
        """
        Build vector documents for a batch of emails.
        """

        if not email_ids:
            return []

        emails = (
            db.query(Email)
            .filter(
                Email.id.in_(email_ids)
            )
            .all()
        )

        email_lookup = {
            email.id: email
            for email in emails
        }

        intelligence_rows = (
            db.query(EmailIntelligence)
            .filter(
                EmailIntelligence.email_id.in_(email_ids)
            )
            .all()
        )

        intelligence_lookup = {
            row.email_id: row
            for row in intelligence_rows
        }

        items = []

        for email_id in email_ids:

            email = email_lookup.get(
                email_id
            )

            if email is None:
                continue

            intelligence = intelligence_lookup.get(
                email_id
            )

            document = cls._build_document(
                email,
                intelligence,
            )

            if not document.strip():
                continue

            items.append(
                {
                    "email_id": email.id,
                    "document": document,
                    "metadata": cls._build_metadata(
                        email,
                        intelligence,
                    ),
                }
            )

        return items

    @classmethod
    def add_email(
        cls,
        db: Session,
        email_id: int,
    ) -> None:
        """
        Index a single email.
        """

        cls.add_batch(
            db=db,
            email_ids=[email_id],
        )

    @classmethod
    def add_batch(
        cls,
        db: Session,
        email_ids: list[int],
    ) -> int:
        """
        Batch index multiple emails.

        Returns:
            Number of indexed emails.
        """

        items = cls.build_batch(
            db=db,
            email_ids=email_ids,
        )

        if not items:
            logger.info(
                "No emails available for vector indexing."
            )
            return 0

        vector_store.upsert_many(
            items=items,
        )

        logger.info(
            "Indexed %s email(s) into Chroma.",
            len(items),
        )

        return len(items)

    @classmethod
    def update_email(
        cls,
        db: Session,
        email_id: int,
    ) -> None:
        cls.add_email(
            db=db,
            email_id=email_id,
        )

    @classmethod
    def delete_email(
        cls,
        email_id: int,
    ) -> None:
        vector_store.delete(
            email_id,
        )

    @classmethod
    def similarity_search(
        cls,
        db: Session,
        query: str,
        limit: int = 5,
    ) -> list[Email]:
        """
        Retrieve similar emails using Chroma and return
        the corresponding Email models.
        """

        matches = vector_store.similarity_search(
            query=query,
            limit=limit,
        )

        email_ids = [
            item["email_id"]
            for item in matches
        ]

        if not email_ids:
            return []

        emails = (
            db.query(Email)
            .filter(
                Email.id.in_(email_ids),
            )
            .all()
        )

        lookup = {
            email.id: email
            for email in emails
        }

        return [
            lookup[email_id]
            for email_id in email_ids
            if email_id in lookup
        ]

    @classmethod
    def reindex_all(
        cls,
        db: Session,
    ) -> int:
        """
        Rebuild the entire Chroma collection.
        """

        emails = (
            db.query(Email)
            .order_by(
                Email.id,
            )
            .all()
        )

        email_ids = [
            email.id
            for email in emails
        ]

        return cls.add_batch(
            db=db,
            email_ids=email_ids,
        )