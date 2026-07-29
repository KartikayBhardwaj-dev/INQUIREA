from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.email import Email
from backend.app.models.email_intelligence import EmailIntelligence
from backend.app.repositories.email_embedding_repository import (
    EmailEmbeddingRepository,
)

logger = logging.getLogger(__name__)


class ChatRetriever:
    """
    Semantic retrieval engine for AI Inbox Chat.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = EmailEmbeddingRepository(db)

    def _load_intelligence_map(
        self,
        email_ids: Iterable[int],
    ) -> dict[int, EmailIntelligence]:
        ids = list(email_ids)
        if not ids:
            return {}

        intelligence_rows = (
            self.db.query(EmailIntelligence)
            .filter(EmailIntelligence.email_id.in_(ids))
            .all()
        )

        return {row.email_id: row for row in intelligence_rows}

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        sender: Optional[str] = None,
        requires_reply: Optional[bool] = None,
        sort_by: str = "relevance",
        date_from=None,
        date_to=None,
    ) -> list[Email]:
        """
        Production semantic retrieval with SQL metadata filtering.
        """
        try:
            return self.repository.similarity_search(
                query=query,
                limit=limit,
                user_id=user_id,
                category=category,
                priority=priority,
                sender=sender,
                requires_reply=requires_reply,
                date_from=date_from,
                date_to=date_to,
                sort_by=sort_by,
            )
        except Exception:
            logger.exception("Error during semantic chat retrieval for query: '%s'", query)
            return []

    def load_email_data(
        self,
        emails: list[Email],
    ) -> list[tuple[Email, EmailIntelligence | None]]:
        """
        Batch-loads EmailIntelligence records for a list of emails to avoid N+1 queries.
        """
        if not emails:
            return []

        intelligence_map = self._load_intelligence_map(email.id for email in emails)

        return [(email, intelligence_map.get(email.id)) for email in emails]