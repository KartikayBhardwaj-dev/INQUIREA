import logging

from chromadb import PersistentClient

from backend.app.core.config import get_settings
from backend.app.core.embeddings import embeddings


logger = logging.getLogger(__name__)

settings = get_settings()


class VectorStore:
    """
    Thin wrapper around ChromaDB.

    Responsible only for:

    • add/update vectors
    • batch indexing
    • delete vectors
    • similarity search

    PostgreSQL remains the source of truth.
    """

    def __init__(self):
        self.client = PersistentClient(
            path=settings.CHROMA_PATH,
        )

        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
        )

    def upsert(
        self,
        *,
        email_id: int,
        document: str,
        metadata: dict,
    ) -> None:
        """
        Insert or update a single vector.
        """

        embedding = embeddings.embed_query(
            document,
        )

        self.collection.upsert(
            ids=[str(email_id)],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata],
        )

        logger.debug(
            "Indexed email %s",
            email_id,
        )

    def upsert_many(
        self,
        *,
        items: list[dict],
    ) -> None:
        """
        Batch insert/update vectors.

        Each item:

        {
            "email_id": int,
            "document": str,
            "metadata": dict,
        }
        """

        if not items:
            return

        ids = [
            str(item["email_id"])
            for item in items
        ]

        documents = [
            item["document"]
            for item in items
        ]

        metadatas = [
            item["metadata"]
            for item in items
        ]

        embeddings_list = embeddings.embed_documents(
            documents,
        )

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings_list,
            metadatas=metadatas,
        )

        logger.info(
            "Indexed %s vectors.",
            len(items),
        )

    def delete(
        self,
        email_id: int,
    ) -> None:
        """
        Delete a vector by email id.
        """

        self.collection.delete(
            ids=[str(email_id)],
        )

        logger.debug(
            "Deleted vector %s",
            email_id,
        )

    def similarity_search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        """
        Semantic search.
        """

        query_embedding = embeddings.embed_query(
            query,
        )

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
        )

        matches = []

        ids = results.get(
            "ids",
            [[]],
        )[0]

        docs = results.get(
            "documents",
            [[]],
        )[0]

        metas = results.get(
            "metadatas",
            [[]],
        )[0]

        distances = results.get(
            "distances",
            [[]],
        )[0]

        for (
            email_id,
            document,
            metadata,
            distance,
        ) in zip(
            ids,
            docs,
            metas,
            distances,
        ):
            matches.append(
                {
                    "email_id": int(email_id),
                    "document": document,
                    "metadata": metadata,
                    "distance": distance,
                }
            )

        return matches

    def count(
        self,
    ) -> int:
        """
        Number of indexed vectors.
        """

        return self.collection.count()

    def reset(
        self,
    ) -> None:
        """
        Drop and recreate the Chroma collection.
        """

        self.client.delete_collection(
            settings.CHROMA_COLLECTION,
        )

        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
        )

        logger.warning(
            "Reset Chroma collection '%s'.",
            settings.CHROMA_COLLECTION,
        )


vector_store = VectorStore()