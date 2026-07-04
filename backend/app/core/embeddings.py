from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from backend.app.core.config import get_settings


settings = get_settings()


@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Singleton embedding model used across INQUIREA.

    Shared by:

    • Vector Memory
    • Semantic Search
    • Inbox Chat (RAG)
    • Future Knowledge Retrieval
    """

    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu",
        },
        encode_kwargs={
            "normalize_embeddings": True,
        },
    )


embeddings = get_embeddings()