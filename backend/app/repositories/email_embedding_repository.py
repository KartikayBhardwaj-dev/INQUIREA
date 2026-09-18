from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.app.core.embeddings import embeddings
from backend.app.models.email import Email
from backend.app.models.email_embedding import EmailEmbedding

logger = logging.getLogger(__name__)


class EmailEmbeddingRepository:
    """
    Repository responsible for storing and retrieving
    semantic email embeddings using PostgreSQL + pgvector.
    """

    def __init__(self, db: Session):
        self.db = db

    def upsert(self, *, email_id: int, document: str, metadata: dict) -> None:
        """
        Insert or update a single embedding.
        """
        vector = list(embeddings.embed_query(document))
        
        # Use Core table directly to prevent ORM attribute name conflicts
        table = EmailEmbedding.__table__
        stmt = insert(table)
        excluded = stmt.excluded

        stmt = stmt.values(
            email_id=email_id,
            embedding=vector,
            document=document,
            metadata=metadata,
            updated_at=datetime.utcnow(),
        ).on_conflict_do_update(
            index_elements=["email_id"],
            set_={
                "embedding": excluded.embedding,
                "document": excluded.document,
                "metadata": excluded.metadata,
                "updated_at": datetime.utcnow(),
            },
        )
        self.db.execute(stmt)
        logger.debug("Indexed email %s", email_id)

    def upsert_many(self, *, items: list[dict]) -> None:
        """
        Batch insert/update embeddings.
        """
        if not items:
            return

        documents = [item["document"] for item in items]
        embedding_vectors = embeddings.embed_documents(documents)
        rows = []

        for item, vector in zip(items, embedding_vectors):
            rows.append(
                {
                    "email_id": item["email_id"],
                    "embedding": list(vector),
                    "document": item["document"],
                    "metadata": item["metadata"],
                    "updated_at": datetime.utcnow(),
                }
            )

        # Target Core Table to ensure clean bulk dictionary mapping
        table = EmailEmbedding.__table__
        stmt = insert(table)
        excluded = stmt.excluded

        stmt = stmt.values(rows).on_conflict_do_update(
            index_elements=["email_id"],
            set_={
                "embedding": excluded.embedding,
                "document": excluded.document,
                "metadata": excluded.metadata,
                "updated_at": datetime.utcnow(),
            },
        )
        self.db.execute(stmt)
        logger.info("Indexed %s email(s).", len(rows))

    def delete(self, email_id: int) -> None:
        """
        Delete an email embedding.
        """
        self.db.query(EmailEmbedding).filter(EmailEmbedding.email_id == email_id).delete(synchronize_session=False)
        logger.debug("Deleted embedding for email %s", email_id)

    def similarity_search(
    self,
    *,
    query: str,
    limit: int = 5,
    user_id: Optional[int] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    sender: Optional[str] = None,
    email_reference: Optional[str] = None,
    requires_reply: Optional[bool] = None,
        date_from: Any = None,
        date_to: Any = None,
        sort_by: str = "relevance",
        filter_operator: str = "AND",
    ) -> list[Email]:
        """
        Production semantic retrieval combining filtering and hybrid scoring.
        """
        query_embedding = list(embeddings.embed_query(query))

        sql = """
        SELECT e.*
        FROM email_embeddings emb
        JOIN emails e ON e.id = emb.email_id
        LEFT JOIN email_intelligence intel ON intel.email_id = e.id
        WHERE 1=1
        """

        params: dict[str, Any] = {
            "embedding": str(query_embedding),
            "limit": limit,
            "keyword": f"%{query}%",
        }

        if user_id is not None:
            sql += "\nAND e.user_id = :user_id"
            params["user_id"] = user_id
        logger.warning(
    "RETRIEVAL DEBUG | user_id=%r | email_reference=%r | query=%r",
    user_id,
    email_reference,
    query,
)
        metadata_conditions: list[str] = []
        if email_reference:
            sql += """
    AND (
        LOWER(e.sender) LIKE LOWER(:email_reference)
        OR
        LOWER(e.subject) LIKE LOWER(:email_reference)
    )
    """
            params["email_reference"] = f"%{email_reference.strip()}%"
        if category:
            metadata_conditions.append(
        "LOWER(intel.category) = LOWER(:category)"
    )
            params["category"] = category

        if priority:
            metadata_conditions.append(
        "LOWER(intel.priority) = LOWER(:priority)"
    )
            params["priority"] = priority

        if sender:
            metadata_conditions.append(
        "LOWER(e.sender) LIKE LOWER(:sender)"
    )
            params["sender"] = f"%{sender}%"
        
        if requires_reply is not None:
            metadata_conditions.append(
        "CAST(intel.extracted_data->>'requires_reply' AS BOOLEAN) = :requires_reply"
    )
            params["requires_reply"] = requires_reply

        if metadata_conditions:
            operator = (
        "OR"
        if filter_operator.upper() == "OR"
        else "AND"
    )

            sql += (
        "\nAND ("
        + f" {operator} ".join(metadata_conditions)
        + ")"
    )

        if date_from:
            sql += "\nAND e.received_at >= :date_from"
            params["date_from"] = date_from

        if date_to:
            sql += "\nAND e.received_at <= :date_to"
            params["date_to"] = date_to

        if sort_by == "date":
            sql += "\nORDER BY e.received_at DESC"
        elif sort_by == "priority":
            sql += """
            \nORDER BY
            CASE LOWER(intel.priority)
                WHEN 'urgent' THEN 4
                WHEN 'high' THEN 3
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 1
                ELSE 0
            END DESC
            """
        else:
            # Hybrid search calculation: Combine 70% vector distance + 30% text keyword match
            sql += """
            \nORDER BY (
                (emb.embedding <=> CAST(:embedding AS vector)) * 0.7 +
                (CASE WHEN LOWER(emb.document) LIKE LOWER(:keyword) THEN 0.0 ELSE 0.3 END) * 0.3
            ) ASC
            """

        sql += "\nLIMIT :limit"
        logger.warning(
    "RETRIEVAL SQL DEBUG:\n%s\nPARAMS=%r",
    sql,
    params,
)
        return self.db.query(Email).from_statement(text(sql)).params(**params).all()

    def count(self) -> int:
        return self.db.query(func.count(EmailEmbedding.id)).scalar() or 0

    def reset(self) -> None:
        self.db.query(EmailEmbedding).delete(synchronize_session=False)
        logger.warning("Deleted all email embeddings.")


def get_email_embedding_repository(db: Session) -> EmailEmbeddingRepository:
    return EmailEmbeddingRepository(db)


def create_repository(db: Session) -> EmailEmbeddingRepository:
    return EmailEmbeddingRepository(db)
