from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.services.chat_retriever import ChatRetriever


class EmailToolService:
    """
    Shared service for Level 2 Email Tools.

    Responsibilities
    ----------------
    - Wrap existing retrieval pipeline.
    - Reuse ChatRetriever.
    - Return JSON-friendly responses.
    - Contain NO SQL.
    - Contain NO repository logic.
    - Contain NO LLM logic.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.retriever = ChatRetriever(db)

    # ---------------------------------------------------------
    # Search Emails
    # ---------------------------------------------------------

    def search_emails(
        self,
        query: str,
        limit: int = 5,
        category: str | None = None,
        priority: str | None = None,
        sender: str | None = None,
        requires_reply: bool | None = None,
        sort_by: str = "relevance",
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:

        emails = self.retriever.retrieve(
            query=query,
            limit=limit,
            category=category,
            priority=priority,
            sender=sender,
            requires_reply=requires_reply,
            sort_by=sort_by,
            date_from=date_from,
            date_to=date_to,
        )

        email_data = self.retriever.load_email_data(
            emails,
        )

        return [
            self._serialize_email(email, intelligence)
            for email, intelligence in email_data
        ]

    # ---------------------------------------------------------
    # Get Single Email
    # ---------------------------------------------------------

    def get_email(
        self,
        email_id: int,
    ) -> dict | None:

        results = self.search_emails(
            query="",
            limit=100,
        )

        for email in results:
            if email["email_id"] == email_id:
                return email

        return None

    # ---------------------------------------------------------
    # Summarize Thread (placeholder)
    # ---------------------------------------------------------

    def summarize_thread(
        self,
        thread_id: str,
    ) -> dict:

        return {
            "thread_id": thread_id,
            "status": "not_implemented",
        }

    # ---------------------------------------------------------
    # List Emails Requiring Reply
    # ---------------------------------------------------------

    def list_reply_required(
        self,
        limit: int = 20,
    ) -> list[dict]:

        return self.search_emails(
            query="",
            limit=limit,
            requires_reply=True,
        )

    # ---------------------------------------------------------
    # Serialization Helper
    # ---------------------------------------------------------

    def _serialize_email(
    self,
    email,
    intelligence,
) -> dict:

        extracted = {}

        if (
        intelligence
        and intelligence.extracted_data
    ):
            extracted = intelligence.extracted_data

        entities = extracted.get(
        "extracted_entities",
        extracted.get(
            "entities",
            {},
        ),
    )

        return {
        # Local database ID
        "email_id": email.id,

        # Actual Gmail message ID
        "gmail_message_id": email.gmail_message_id,

        "subject": email.subject,
        "sender": email.sender,
        "recipient": email.recipient,
        "received_at": email.received_at,

        "category": (
            intelligence.category
            if intelligence
            else None
        ),

        "priority": (
            intelligence.priority
            if intelligence
            else None
        ),

        "summary": (
            intelligence.summary
            if intelligence
            else None
        ),

        "requires_reply": extracted.get(
            "requires_reply",
            False,
        ),

        "entities": entities,

        "action_items": (
            entities.get(
                "action_items",
                [],
            )
            if isinstance(
                entities,
                dict,
            )
            else []
        ),
    }