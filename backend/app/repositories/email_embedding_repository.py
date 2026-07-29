# import logging
# from datetime import datetime

# from sqlalchemy.dialects.postgresql import insert
# from sqlalchemy.orm import Session

# from backend.app.core.embeddings import embeddings
# from backend.app.models.email_embedding import EmailEmbedding
# from sqlalchemy import func
# from sqlalchemy import text
# logger = logging.getLogger(__name__)
# from backend.app.models.email import Email

# class EmailEmbeddingRepository:
#     """
#     Repository responsible for storing and retrieving
#     semantic email embeddings using PostgreSQL + pgvector.

#     PostgreSQL is the single source of truth.

#     Responsibilities
#     ----------------
#     - Upsert embeddings
#     - Batch upsert embeddings
#     - Delete embeddings
#     - Similarity search
#     """

#     def __init__(
#         self,
#         db: Session,
#     ):
#         self.db = db

#     # ---------------------------------------------------------
#     # UPSERT
#     # ---------------------------------------------------------

#     def upsert(
#         self,
#         *,
#         email_id: int,
#         document: str,
#         metadata: dict,
#     ) -> None:
#         """
#         Insert or update a single embedding.
#         """

#         embedding = list(
#             embeddings.embed_query(document)
#         )

#         stmt = insert(
#             EmailEmbedding
#         )

#         excluded = stmt.excluded

#         stmt = (
#             stmt.values(
#                 email_id=email_id,
#                 embedding=embedding,
#                 document=document,
#                 metadata_json=metadata,
#                 updated_at=datetime.utcnow(),
#             )
#             .on_conflict_do_update(
#     index_elements=["email_id"],
#     set_={
#         EmailEmbedding.embedding: excluded.embedding,
#         EmailEmbedding.document: excluded.document,
#         EmailEmbedding.metadata_json: excluded.metadata,
#         EmailEmbedding.updated_at: datetime.utcnow(),
#     },
# )
#         )

#         self.db.execute(stmt)

#         logger.debug(
#             "Indexed email %s",
#             email_id,
#         )

#     # ---------------------------------------------------------
#     # BATCH UPSERT
#     # ---------------------------------------------------------

#     def upsert_many(
#         self,
#         *,
#         items: list[dict],
#     ) -> None:
#         """
#         Batch insert/update embeddings.
#         """

#         if not items:
#             return

#         documents = [
#             item["document"]
#             for item in items
#         ]

#         embedding_vectors = embeddings.embed_documents(
#             documents,
#         )

#         rows = []

#         for item, embedding in zip(
#             items,
#             embedding_vectors,
#         ):
#             rows.append(
#                 {
#                     "email_id": item["email_id"],
#                     "embedding": list(embedding),
#                     "document": item["document"],
#                     "metadata_json": item["metadata"],
#                     "updated_at": datetime.utcnow(),
#                 }
#             )

#         stmt = insert(
#             EmailEmbedding
#         )

#         excluded = stmt.excluded

#         stmt = (
#             stmt.values(rows)
#             .on_conflict_do_update(
#     index_elements=["email_id"],
#     set_={
#         EmailEmbedding.embedding: excluded.embedding,
#         EmailEmbedding.document: excluded.document,
#         EmailEmbedding.metadata_json: excluded.metadata,
#         EmailEmbedding.updated_at: datetime.utcnow(),
#     },
# )
#         )

#         self.db.execute(stmt)

#         logger.info(
#             "Indexed %s email(s).",
#             len(rows),
#         )

#         # ---------------------------------------------------------
#     # DELETE
#     # ---------------------------------------------------------

#     def delete(
#         self,
#         email_id: int,
#     ) -> None:
#         """
#         Delete an email embedding.
#         """

#         (
#             self.db.query(EmailEmbedding)
#             .filter(
#                 EmailEmbedding.email_id == email_id,
#             )
#             .delete(
#                 synchronize_session=False,
#             )
#         )

#         logger.debug(
#             "Deleted embedding for email %s",
#             email_id,
#         )

#     # ---------------------------------------------------------
#     # SIMILARITY SEARCH
#     # ---------------------------------------------------------

#     def similarity_search(
#     self,
#     *,
#     query: str,
#     limit: int = 5,
#     category: str | None = None,
#     priority: str | None = None,
#     sender: str | None = None,
#     requires_reply: bool | None = None,
#     date_from=None,
#     date_to=None,
#     sort_by: str = "relevance",
# ) -> list:


#         """
#     Production semantic retrieval.

#     Single SQL query.

#     pgvector
#         +
#     emails
#         +
#     email_intelligence
#     """
    

#         query_embedding = list(
#         embeddings.embed_query(query)
#     )

#         sql = """
#     SELECT
#         e.*
#     FROM email_embeddings emb

#     JOIN emails e
#         ON e.id = emb.email_id

#     LEFT JOIN email_intelligence intel
#         ON intel.email_id = e.id

#     WHERE 1=1
#     """

#         params = {
#         "embedding": str(query_embedding),
#         "limit": limit,
#     }

#         if category:
#             sql += """
#         AND LOWER(intel.category)=LOWER(:category)
#         """
#             params["category"] = category

#         if priority:
#             sql += """
#         AND LOWER(intel.priority)=LOWER(:priority)
#         """
#             params["priority"] = priority

#         if sender:
#             sql += """
#         AND LOWER(e.sender)
#             LIKE LOWER(:sender)
#         """
#             params["sender"] = f"%{sender}%"

#         if requires_reply is not None:
#             sql += """
#         AND CAST(
#             intel.extracted_data->>'requires_reply'
#             AS BOOLEAN
#         ) = :requires_reply
#         """
#             params["requires_reply"] = requires_reply

#         if date_from:
#             sql += """
#         AND e.received_at >= :date_from
#         """
#             params["date_from"] = date_from

#         if date_to:
#             sql += """
#         AND e.received_at <= :date_to
#         """
#             params["date_to"] = date_to

#         if sort_by == "date":

#             sql += """
#         ORDER BY e.received_at DESC
#         """

#         elif sort_by == "priority":

#             sql += """
#         ORDER BY
#         CASE LOWER(intel.priority)
#             WHEN 'urgent' THEN 4
#             WHEN 'high' THEN 3
#             WHEN 'medium' THEN 2
#             WHEN 'low' THEN 1
#             ELSE 0
#         END DESC
#         """

#         else:

#             sql += """
#         ORDER BY
#         emb.embedding <=> CAST(:embedding AS vector)
#         """

#         sql += """
#     LIMIT :limit
#     """

#         result = self.db.execute(
#         text(sql),
#         params,
#     )

#         return (
#     self.db.query(Email)
#     .from_statement(text(sql))
#     .params(**params)
#     .all()
# )

#     # ---------------------------------------------------------
#     # COUNT
#     # ---------------------------------------------------------

#     def count(
#         self,
#     ) -> int:
#         """
#         Return number of indexed embeddings.
#         """

#         return (
#             self.db.query(
#                 func.count(
#                     EmailEmbedding.id
#                 )
#             )
#             .scalar()
#             or 0
#         )

#     # ---------------------------------------------------------
#     # RESET
#     # ---------------------------------------------------------

#     def reset(
#         self,
#     ) -> None:
#         """
#         Remove every embedding.

#         Primarily used for rebuilds.
#         """

#         (
#             self.db.query(
#                 EmailEmbedding
#             )
#             .delete(
#                 synchronize_session=False,
#             )
#         )

#         logger.warning(
#             "Deleted all email embeddings."
#         )


# # ---------------------------------------------------------
# # Repository Helpers
# # ---------------------------------------------------------


# def get_email_embedding_repository(
#     db: Session,
# ) -> EmailEmbeddingRepository:
#     """
#     Dependency injection helper.
#     """

#     return EmailEmbeddingRepository(db)


# def create_repository(
#     db: Session,
# ) -> EmailEmbeddingRepository:
#     """
#     Factory helper.

#     Useful outside FastAPI dependency injection.
#     """

#     return EmailEmbeddingRepository(db)





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
            metadata_json=metadata,
            updated_at=datetime.utcnow(),
        ).on_conflict_do_update(
            index_elements=["email_id"],
            set_={
                "embedding": excluded.embedding,
                "document": excluded.document,
                "metadata_json": excluded.metadata_json,
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
                    "metadata_json": item["metadata"],
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
                "metadata_json": excluded.metadata_json,
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
        requires_reply: Optional[bool] = None,
        date_from: Any = None,
        date_to: Any = None,
        sort_by: str = "relevance",
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

        if category:
            sql += "\nAND LOWER(intel.category) = LOWER(:category)"
            params["category"] = category

        if priority:
            sql += "\nAND LOWER(intel.priority) = LOWER(:priority)"
            params["priority"] = priority

        if sender:
            sql += "\nAND LOWER(e.sender) LIKE LOWER(:sender)"
            params["sender"] = f"%{sender}%"

        if requires_reply is not None:
            sql += "\nAND CAST(intel.extracted_data->>'requires_reply' AS BOOLEAN) = :requires_reply"
            params["requires_reply"] = requires_reply

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
