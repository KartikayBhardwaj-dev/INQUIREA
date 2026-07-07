from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models.email import Email
from backend.app.models.email_intelligence import (
    EmailIntelligence,
)
from backend.app.services.vector_memory_service import (
    VectorMemoryService,
)


class ChatRetriever:
    """
    Retrieval layer for AI Inbox Chat.

    Responsibilities:
    - Semantic retrieval
    - Metadata filtering
    - Loading Email + EmailIntelligence

    No LLM calls.
    No prompt formatting.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ---------------------------------------------------------
    # Semantic Retrieval
    # ---------------------------------------------------------

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        category: str | None = None,
        priority: str | None = None,
        needs_reply: bool | None = None,
    ) -> list[Email]:
        """
        Retrieve semantically similar emails and optionally
        filter them using structured metadata.
        """

        emails = VectorMemoryService.similarity_search(
            db=self.db,
            query=query,
            limit=limit * 3,
        )

        results: list[Email] = []

        for email in emails:

            intelligence = (
                self.db.query(
                    EmailIntelligence,
                )
                .filter(
                    EmailIntelligence.email_id == email.id,
                )
                .first()
            )

            if intelligence is None:
                continue

            if category:
                if (
                    (intelligence.category or "").lower()
                    != category.lower()
                ):
                    continue

            if priority:
                if (
                    (intelligence.priority or "").lower()
                    != priority.lower()
                ):
                    continue

            if needs_reply is not None:

                extracted = (
                    intelligence.extracted_data
                    or {}
                )

                if (
                    extracted.get(
                        "needs_reply",
                        False,
                    )
                    != needs_reply
                ):
                    continue

            results.append(email)

            if len(results) >= limit:
                break

        return results

    # ---------------------------------------------------------
    # Load Intelligence
    # ---------------------------------------------------------

    def load_email_data(
        self,
        emails: list[Email],
    ) -> list[
        tuple[
            Email,
            EmailIntelligence | None,
        ]
    ]:
        """
        Load EmailIntelligence for each retrieved email.

        Returns:
            [
                (Email, EmailIntelligence),
                ...
            ]
        """

        email_data = []

        for email in emails:

            intelligence = (
                self.db.query(
                    EmailIntelligence,
                )
                .filter(
                    EmailIntelligence.email_id == email.id,
                )
                .first()
            )

            email_data.append(
                (
                    email,
                    intelligence,
                )
            )

        return email_data
