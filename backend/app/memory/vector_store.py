from chromadb import PersistentClient

from backend.app.core.config import get_settings
from backend.app.core.embeddings import embeddings


settings = get_settings()


class VectorStore:
    """
    Thin wrapper around ChromaDB.

    Responsible only for:

    - add/update vectors
    - delete vectors
    - similarity search

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

        embedding = embeddings.embed_query(document)

        self.collection.upsert(
            ids=[str(email_id)],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata],
        )

    def delete(
        self,
        email_id: int,
    ) -> None:

        self.collection.delete(
            ids=[str(email_id)],
        )

    def similarity_search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:

        query_embedding = embeddings.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
        )

        matches = []

        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for email_id, document, metadata, distance in zip(
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

    def count(self) -> int:

        return self.collection.count()

    def reset(self) -> None:

        self.client.delete_collection(
            settings.CHROMA_COLLECTION,
        )

        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
        )


vector_store = VectorStore()