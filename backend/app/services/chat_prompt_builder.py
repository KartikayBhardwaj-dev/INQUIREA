from __future__ import annotations


from backend.app.models.email import Email
from backend.app.models.email_intelligence import (
    EmailIntelligence,
)


class ChatPromptBuilder:
    """
    Builds production-ready RAG prompts for AI Inbox Chat.

    Responsibilities
    ----------------
    - Format retrieved emails
    - Format conversation history
    - Build the final LLM prompt

    No retrieval.
    No database access.
    No LLM calls.
    """

    SYSTEM_PROMPT = """
You are INQUIREA, an AI Email Copilot.

You answer questions ONLY using the retrieved emails provided below.

Rules:

1. Never invent information.

2. Never hallucinate.

3. If the answer is not present in the retrieved emails,
reply exactly:

"I couldn't find that information in your inbox."

4. Be concise but complete.

5. When appropriate, cite:
- Subject
- Sender
- Date

6. If multiple emails answer the question,
summarize them together.

7. Never mention:
- prompts
- embeddings
- retrieval
- vector databases
- internal implementation

Only answer using the retrieved emails.
""".strip()

    # ---------------------------------------------------------
    # Email Formatting
    # ---------------------------------------------------------

    @staticmethod
    def build_email_block(
        email: Email,
        intelligence: EmailIntelligence | None,
    ) -> str:
        """
        Convert a single email into a prompt-friendly block.
        """

        category = (
            intelligence.category
            if intelligence
            else "Unknown"
        )

        priority = (
            intelligence.priority
            if intelligence
            else "Unknown"
        )

        summary = (
            intelligence.summary
            if intelligence
            else ""
        )

        body = (email.body or "").strip()

        if len(body) > 2000:
            body = body[:2000] + "..."

        return f"""
EMAIL {email.id}

Subject:
{email.subject}

Sender:
{email.sender}

Recipient:
{email.recipient}

Date:
{email.received_at}

Category:
{category}

Priority:
{priority}

Summary:
{summary}

Body:
{body}
""".strip()

    @classmethod
    def build_email_context(
        cls,
        email_data: list[
            tuple[
                Email,
                EmailIntelligence | None,
            ]
        ],
    ) -> str:
        """
        Build context from retrieved emails.
        """

        if not email_data:
            return "No relevant emails were found."

        blocks = [
            cls.build_email_block(
                email,
                intelligence,
            )
            for email, intelligence in email_data
        ]

        return "\n\n" + (
            "\n\n" + "=" * 80 + "\n\n"
        ).join(blocks)

    # ---------------------------------------------------------
    # Conversation Formatting
    # ---------------------------------------------------------

    @staticmethod
    def build_conversation_context(
    history: list[dict],
) -> str:
        """
        Format the last conversation turns.
        """

        if not history:
            return "No previous conversation."

        messages = []

        for message in history:
            role = (
        "User"
        if message["role"] == "user"
        else "Assistant"
    )

        messages.append(
        f"{role}: {message['message']}"
    )

        return "\n".join(messages)

    # ---------------------------------------------------------
    # Final Prompt
    # ---------------------------------------------------------

    @classmethod
    def build_prompt(
    cls,
    question: str,
    conversation: list[dict],
    email_data: list[
            tuple[
                Email,
                EmailIntelligence | None,
            ]
        ],
    ) -> str:
        """
        Build the final production RAG prompt.
        """

        conversation_context = cls.build_conversation_context(
            conversation,
        )

        email_context = cls.build_email_context(
            email_data,
        )

        return f"""
{cls.SYSTEM_PROMPT}

--------------------------------------------------
CONVERSATION
--------------------------------------------------

{conversation_context}

--------------------------------------------------
RETRIEVED EMAILS
--------------------------------------------------

{email_context}

--------------------------------------------------
QUESTION
--------------------------------------------------

{question}

--------------------------------------------------
ANSWER
--------------------------------------------------
""".strip()