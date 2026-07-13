from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from backend.app.models.email import Email
from backend.app.models.email_intelligence import (
    EmailIntelligence,
)
from backend.app.repositories.email_embedding_repository import (
    EmailEmbeddingRepository,
)


class ChatRetriever:
    """
    Semantic retrieval engine for AI Inbox Chat.

    Architecture
    ------------
    PostgreSQL
        ├── emails
        ├── email_intelligence
        └── email_embeddings (pgvector)

    Responsibilities
    ----------------
    - Coordinate semantic retrieval
    - Delegate vector search to repository
    - Load EmailIntelligence records
    - Return Email models
    - No LLM logic
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.repository = EmailEmbeddingRepository(
            db,
        )

    # ---------------------------------------------------------
    # Helper Methods
    # ---------------------------------------------------------

    def _load_intelligence_map(
        self,
        email_ids: Iterable[int],
    ) -> dict[int, EmailIntelligence]:
        """
        Batch-load EmailIntelligence objects.

        Avoids N+1 queries.
        """

        ids = list(email_ids)

        if not ids:
            return {}

        intelligence_rows = (
            self.db.query(
                EmailIntelligence,
            )
            .filter(
                EmailIntelligence.email_id.in_(ids),
            )
            .all()
        )

        return {
            row.email_id: row
            for row in intelligence_rows
        }

    
    
        # ---------------------------------------------------------
    # Semantic Retrieval
    # ---------------------------------------------------------

    def retrieve(
    self,
    query: str,
    limit: int = 5,
    category: str | None = None,
    priority: str | None = None,
    sender: str | None = None,
    requires_reply: bool | None = None,
    sort_by: str = "relevance",
    date_from=None,
    date_to=None,
) -> list[Email]:
        """
    Production semantic retrieval.

    Filtering and ranking are executed entirely inside PostgreSQL.
    """

        try:

            return self.repository.similarity_search(
            query=query,
            limit=limit,
            category=category,
            priority=priority,
            sender=sender,
            requires_reply=requires_reply,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
        )

        except Exception:
            return []
    
        # ---------------------------------------------------------
    # Load Email + Intelligence
    # ---------------------------------------------------------

    def load_email_data(
        self,
        emails: list[Email],
    ) -> list[tuple[Email, EmailIntelligence | None]]:
        """
        Load EmailIntelligence records for a list of emails.

        Returns
        -------
        [
            (
                Email,
                EmailIntelligence | None,
            ),
            ...
        ]

        Performs a single batch query to avoid N+1 lookups.
        """

        if not emails:
            return []

        intelligence_map = self._load_intelligence_map(
            email.id
            for email in emails
        )

        return [
            (
                email,
                intelligence_map.get(
                    email.id,
                ),
            )
            for email in emails
        ]