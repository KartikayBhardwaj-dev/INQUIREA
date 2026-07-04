from sqlalchemy.orm import Session

from backend.app.memory.vector_store import vector_store

from backend.app.models.email import Email
from backend.app.models.email_intelligence import EmailIntelligence


class VectorMemoryService:
    """
    Business layer for semantic email memory.

    PostgreSQL = Source of Truth
    ChromaDB = Semantic Index
    """

    @staticmethod
    def _build_document(
        email: Email,
        intelligence: EmailIntelligence | None,
    ) -> str:
        """
        Build one semantic document that will be embedded.
        """

        extracted = {}

        if intelligence and intelligence.extracted_data:
            extracted = intelligence.extracted_data

        organizations = extracted.get(
            "organizations",
            [],
        )

        dates = extracted.get(
            "dates",
            [],
        )

        links = extracted.get(
            "links",
            [],
        )

        amounts = extracted.get(
            "amounts",
            [],
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

Organizations:
{", ".join(organizations)}

Dates:
{", ".join(dates)}

Amounts:
{", ".join(map(str, amounts))}

Links:
{", ".join(links)}

Email Body:
{email.body or ""}
""".strip()

    @staticmethod
    def _build_metadata(
        email: Email,
        intelligence: EmailIntelligence | None,
    ) -> dict:

        extracted = {}

        if intelligence and intelligence.extracted_data:
            extracted = intelligence.extracted_data

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
            "needs_reply": extracted.get(
                "needs_reply",
                False,
            ),
        }

    @classmethod
    def add_email(
        cls,
        db: Session,
        email_id: int,
    ) -> None:

        email = db.get(
            Email,
            email_id,
        )

        if email is None:
            raise ValueError(
                f"Email {email_id} not found."
            )

        intelligence = (
            db.query(
                EmailIntelligence,
            )
            .filter(
                EmailIntelligence.email_id == email_id,
            )
            .first()
        )

        vector_store.upsert(
            email_id=email.id,
            document=cls._build_document(
                email,
                intelligence,
            ),
            metadata=cls._build_metadata(
                email,
                intelligence,
            ),
        )

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

        emails = db.query(
            Email,
        ).all()

        count = 0

        for email in emails:
            cls.add_email(
                db=db,
                email_id=email.id,
            )
            count += 1

        return count