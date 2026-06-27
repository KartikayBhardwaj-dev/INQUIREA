from chromadb import PersistentClient

client = PersistentClient(
    path="backend/app/memory/chroma"
)

collection = client.get_or_create_collection(
    name="email_memory"
)


class VectorMemory:

    @staticmethod
    def store(
        email_id: int,
        content: str,
        metadata: dict,
    ):

        collection.upsert(
            ids=[str(email_id)],
            documents=[content],
            metadatas=[metadata],
        )

    @staticmethod
    def search(
        query: str,
        limit: int = 5,
    ):

        results = collection.query(
            query_texts=[query],
            n_results=limit,
        )

        return results