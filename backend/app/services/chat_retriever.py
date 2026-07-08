from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from backend.app.models.email import Email
from backend.app.models.email_intelligence import EmailIntelligence
from backend.app.services.vector_memory_service import (
    VectorMemoryService,
)


class ChatRetriever:
    """
    Retrieval engine for AI Inbox Chat.

    Responsibilities
    ----------------
    - Semantic retrieval using vector search
    - Metadata filtering
    - Ranking
    - Loading EmailIntelligence
    - Returning Email objects

    This class performs NO LLM calls and NO prompt generation.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ---------------------------------------------------------
    # Helper Methods
    # ---------------------------------------------------------

    def _load_intelligence_map(
        self,
        email_ids: Iterable[int],
    ) -> dict[int, EmailIntelligence]:
        """
        Batch load EmailIntelligence records.

        Returns:
            {
                email_id: EmailIntelligence,
                ...
            }

        Avoids N+1 database queries.
        """

        ids = list(email_ids)

        if not ids:
            return {}

        intelligence_records = (
            self.db.query(
                EmailIntelligence,
            )
            .filter(
                EmailIntelligence.email_id.in_(ids),
            )
            .all()
        )

        return {
            record.email_id: record
            for record in intelligence_records
        }

    def _remove_duplicate_emails(
        self,
        emails: list[Email],
    ) -> list[Email]:
        """
        Remove duplicate emails while preserving order.
        """

        seen: set[int] = set()
        unique: list[Email] = []

        for email in emails:

            if email.id in seen:
                continue

            seen.add(email.id)
            unique.append(email)

        return unique

    def _normalize_text(
        self,
        value: str | None,
    ) -> str:
        """
        Normalize text for case-insensitive comparisons.
        """

        if value is None:
            return ""

        return value.strip().lower()
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
        date_from: str | None = None,
        date_to: str |None = None,
    ) -> list[Email]:
        """
        Retrieve candidate emails from the vector store.

        This step performs ONLY semantic retrieval.

        Metadata filtering, ranking, and sorting are handled in
        later stages.
        """

        # ---------------------------------------------
        # Retrieve semantic candidates
        # ---------------------------------------------

        try:

            candidates = VectorMemoryService.similarity_search(
                db=self.db,
                query=query,
                limit=max(limit * 5, 20),
            )

        except Exception:

            # Missing embeddings / Chroma unavailable
            return []

        if not candidates:
            return []

        # ---------------------------------------------
        # Remove duplicate emails
        # ---------------------------------------------

        candidates = self._remove_duplicate_emails(
            candidates,
        )

        # ---------------------------------------------
        # Batch load EmailIntelligence
        # ---------------------------------------------

        intelligence_map = self._load_intelligence_map(
            email.id
            for email in candidates
        )

        # Keep only emails that actually have intelligence.
        # These are required by later filtering stages.

        candidates = [
            email
            for email in candidates
            if email.id in intelligence_map
        ]

        if not candidates:
            return []

        # ---------------------------------------------
        # Part 3 will continue from here
        # ---------------------------------------------

                # ---------------------------------------------
        # Metadata Filtering
        # ---------------------------------------------

        filtered: list[Email] = []

        for email in candidates:

            intelligence = intelligence_map.get(email.id)

            if intelligence is None:
                continue

            extracted = intelligence.extracted_data or {}

            # -----------------------------------------
            # Category
            # -----------------------------------------

            if category:

                if (
                    self._normalize_text(intelligence.category)
                    != self._normalize_text(category)
                ):
                    continue

            # -----------------------------------------
            # Priority
            # -----------------------------------------

            if priority:

                if (
                    self._normalize_text(intelligence.priority)
                    != self._normalize_text(priority)
                ):
                    continue

            # -----------------------------------------
            # Sender
            # -----------------------------------------

            if sender:

                sender_text = self._normalize_text(email.sender)

                if self._normalize_text(sender) not in sender_text:
                    continue

            # -----------------------------------------
            # Requires Reply
            # -----------------------------------------

            if requires_reply is not None:

                if (
                    extracted.get("requires_reply", False)
                    != requires_reply
                ):
                    continue

            # -----------------------------------------
            # Date Range
            # -----------------------------------------

            if date_from:

                if (
                    email.received_at
                    and email.received_at.isoformat() < date_from
                ):
                    continue

            if date_to:

                if (
                    email.received_at
                    and email.received_at.isoformat() > date_to
                ):
                    continue

            filtered.append(email)

        if not filtered:
            return []

        # ---------------------------------------------
        # Part 4 will continue from here
        # ---------------------------------------------

                # ---------------------------------------------
        # Ranking
        # ---------------------------------------------

        if sort_by == "date":

            filtered.sort(
                key=lambda email: (
                    email.received_at is None,
                    email.received_at,
                ),
                reverse=True,
            )

        elif sort_by == "priority":

            priority_order = {
                "urgent": 4,
                "high": 3,
                "medium": 2,
                "low": 1,
            }

            filtered.sort(
                key=lambda email: priority_order.get(
                    self._normalize_text(
                        intelligence_map[email.id].priority,
                    ),
                    0,
                ),
                reverse=True,
            )

        else:
            # -----------------------------------------
            # Relevance
            # -----------------------------------------
            # Preserve vector search ordering.
            # VectorMemoryService already returns
            # results ranked by semantic similarity.
            pass

        # ---------------------------------------------
        # Final Top-K
        # ---------------------------------------------

        return filtered[:limit]
    def load_email_data(
    self,
    emails: list[Email],
) -> list[tuple[Email, EmailIntelligence | None]]:
        """
    Load EmailIntelligence for retrieved emails.

    Returns
    -------
    [
        (Email, EmailIntelligence | None),
        ...
    ]
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
            intelligence_map.get(email.id),
        )
        for email in emails
    ]