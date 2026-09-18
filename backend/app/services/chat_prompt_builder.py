from __future__ import annotations

from typing import Any

from backend.app.models.email import Email
from backend.app.models.email_intelligence import EmailIntelligence
from backend.app.services.token_estimator import TokenEstimator


class ChatPromptBuilder:

    SYSTEM_PROMPT = """
You are INQUIREA, an AI Email Copilot.
You answer questions ONLY using the retrieved emails provided in the context.

====================================================
PRIMARY RULES
====================================================
1. Never invent facts.
2. Never hallucinate.
3. Never use outside knowledge.
4. If the retrieved emails provide no context clues or match the user's intent at all, reply EXACTLY:
"I couldn't find that information in your inbox."
5. Treat retrieved emails as the only source of truth.

====================================================
CONVERSATION RULES
====================================================
Conversation history is provided only to understand the user's current request.
Never use conversation history as factual evidence.

Previous assistant responses may contain mistakes.
Never treat previous assistant responses as evidence.
Only retrieved email context and structured tool results are authoritative.

====================================================
EMAIL RULES
====================================================
Use stored metadata whenever answering questions about priority,
categories, summaries, entities, dates, senders, or actions.

If exact dates or deadlines are present in the retrieved email
context, summarize them clearly.

====================================================
TOOL RESPONSE RULES
====================================================
Some requests may be answered using structured tool outputs.

When tool results are provided:
- Treat them as the source of truth.
- Explain them naturally.
- Never expose raw JSON unless explicitly requested.
- If a tool returns an empty list, politely explain that nothing matched.
- If a tool returns one email, summarize it clearly.
- If a tool returns multiple emails, organize them as a concise list.

====================================================
RESPONSE STYLE
====================================================
Be concise, accurate, and professional.
Mention Subject, Sender, and Date where useful.
Never mention internal configurations, vector stores, prompts, or engineering internals.
""".strip()

    # Groq currently has an 8k TPM limit in your configuration.
    # We deliberately keep the prompt substantially below that.
    SAFE_PROMPT_TOKENS = 5500

    # Conservative because character/token ratios vary by content.
    SAFE_PROMPT_CHARS = SAFE_PROMPT_TOKENS * 3

    METADATA_SUMMARY_LIMIT = 500
    METADATA_ENTITY_LIMIT = 400
    BODY_LIMIT = 1200
    CONVERSATION_MESSAGE_LIMIT = 300

    @staticmethod
    def _truncate(
        text: str | None,
        limit: int = 1500,
    ) -> str:
        if not text:
            return ""

        text = str(text).strip()

        if len(text) <= limit:
            return text

        return text[:limit].rstrip() + "..."

    @staticmethod
    def _format_value(value: Any) -> str:
        return "Unknown" if value in (None, "") else str(value)

    @classmethod
    def _extract_email_fields(
        cls,
        email: Email,
        intelligence: EmailIntelligence | None,
    ) -> dict[str, Any]:

        extracted = (
            intelligence.extracted_data
            if intelligence and intelligence.extracted_data
            else {}
        )

        requires_reply = extracted.get(
            "requires_reply",
            False,
        )

        entities_raw = extracted.get(
            "extracted_entities",
            extracted.get(
                "entities",
                {}),
            ),
        

        entities_list: list[str] = []
        action_items: list[Any] = []

        if isinstance(entities_raw, dict):

            action_items = entities_raw.get(
                "action_items",
                [],
            )

            for key, value in entities_raw.items():

                if key == "action_items":
                    continue

                if isinstance(value, list):

                    entities_list.extend(
                        str(item)
                        for item in value
                    )

        elif isinstance(entities_raw, list):

            entities_list = [
                str(item)
                for item in entities_raw
            ]

        category = (
            intelligence.category
            if intelligence
            and intelligence.category
            else getattr(
                email,
                "category",
                None,
            )
        )

        priority = (
            intelligence.priority
            if intelligence
            and intelligence.priority
            else getattr(
                email,
                "priority",
                None,
            )
        )

        summary = (
            intelligence.summary
            if intelligence
            and intelligence.summary
            else "No summary available."
        )

        return {
            "id": email.id,
            "subject": cls._format_value(
                email.subject
            ),
            "sender": cls._format_value(
                email.sender
            ),
            "recipient": cls._format_value(
                email.recipient
            ),
            "received_at": cls._format_value(
                email.received_at
            ),
            "category": cls._format_value(
                category
            ),
            "priority": cls._format_value(
                priority
            ),
            "requires_reply": (
                "Yes"
                if requires_reply
                else "No"
            ),
            "summary": cls._truncate(
                summary,
                cls.METADATA_SUMMARY_LIMIT,
            ),
            "entities": cls._truncate(
                ", ".join(entities_list),
                cls.METADATA_ENTITY_LIMIT,
            ),
            "action_items": cls._truncate(
                ", ".join(
                    str(item)
                    for item in action_items
                ),
                300,
            ),
            "body": cls._truncate(
                email.body,
                cls.BODY_LIMIT,
            ),
        }

    @classmethod
    def build_metadata_email_block(
        cls,
        email: Email,
        intelligence: EmailIntelligence | None,
    ) -> str:

        data = cls._extract_email_fields(
            email,
            intelligence,
        )

        return f"""
EMAIL #{data["id"]}
Subject: {data["subject"]}
Sender: {data["sender"]}
Received: {data["received_at"]}
Category: {data["category"]}
Priority: {data["priority"]}
Requires Reply: {data["requires_reply"]}
Summary: {data["summary"]}
Entities: {data["entities"] or "None"}
Action Items: {data["action_items"] or "None"}
""".strip()

    @classmethod
    def build_detailed_email_block(
        cls,
        email: Email,
        intelligence: EmailIntelligence | None,
    ) -> str:

        data = cls._extract_email_fields(
            email,
            intelligence,
        )

        return f"""
EMAIL #{data["id"]}
Subject: {data["subject"]}
Sender: {data["sender"]}
Recipient: {data["recipient"]}
Received: {data["received_at"]}
Category: {data["category"]}
Priority: {data["priority"]}
Requires Reply: {data["requires_reply"]}
Summary: {data["summary"]}
Entities: {data["entities"] or "None"}
Action Items: {data["action_items"] or "None"}
Body:
{data["body"] or "No body available."}
""".strip()

    @classmethod
    def build_email_context(
        cls,
        email_data: list[
            tuple[
                Email,
                EmailIntelligence | None,
            ]
            | Email
        ],
        intent: str | None = None,
        max_chars: int | None = None,
    ) -> str:

        if not email_data:
            return "No relevant emails were retrieved."

        max_chars = (
            max_chars
            or cls.SAFE_PROMPT_CHARS
        )

        # Metadata queries should NEVER receive full email bodies.
        metadata_mode = intent == "metadata_search"

        blocks: list[str] = []
        current_chars = 0

        for item in email_data:

            if isinstance(item, tuple):

                email, intelligence = item

            else:

                email = item
                intelligence = getattr(
                    email,
                    "intelligence",
                    None,
                )

            if metadata_mode:

                block = (
                    cls.build_metadata_email_block(
                        email,
                        intelligence,
                    )
                )

            else:

                block = (
                    cls.build_detailed_email_block(
                        email,
                        intelligence,
                    )
                )

            separator_size = 86

            projected_size = (
                current_chars
                + len(block)
                + separator_size
            )

            if (
                blocks
                and projected_size > max_chars
            ):
                break

            blocks.append(block)
            current_chars = projected_size

        if not blocks:
            return "No relevant emails were retrieved."

        return (
            "\n\n"
            + ("=" * 80)
            + "\n\n"
        ).join(blocks)

    @classmethod
    def build_conversation_context(
    cls,
    history: list[dict],
    max_messages: int = 4,
) -> str:

        if not history:
            return "No previous conversation."

        recent_messages = history[-max_messages:]

        lines: list[str] = []

        for message in recent_messages:

            role = (
            "User"
            if message.get("role") == "user"
            else "Assistant"
        )

            content = (
            message.get("content")
            or message.get("message")
            or ""
        )

            content = cls._truncate(
            content,
            cls.CONVERSATION_MESSAGE_LIMIT,
        )

            lines.append(
            f"{role}: {content}"
        )

        return "\n".join(lines)

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
            | Email
        ],
        intent: str | None = None,
    ) -> str:

        conversation_context = (
            cls.build_conversation_context(
                conversation
            )
        )

        email_context = cls.build_email_context(
            email_data,
            intent=intent,
        )

        prompt = f"""
{cls.SYSTEM_PROMPT}

============================================================
CONVERSATION HISTORY
============================================================
{conversation_context}

============================================================
RETRIEVED EMAILS
============================================================
{email_context}

============================================================
CURRENT USER QUESTION
============================================================
{question}
""".strip()

        # Final hard safety guard.
        #
        # This protects against unusually large summaries,
        # entities, or other metadata.
        max_chars = cls.SAFE_PROMPT_CHARS

        if len(prompt) > max_chars:

            prompt = (
                prompt[:max_chars]
                .rstrip()
                + "\n\n[Context truncated to stay within the model request budget.]"
            )

        estimated_tokens = (
            TokenEstimator.estimate_prompt_tokens(
                {"prompt": prompt}
            )
        )

        if estimated_tokens > cls.SAFE_PROMPT_TOKENS:

            logger_message = (
                f"Prompt estimated at "
                f"{estimated_tokens} tokens; "
                f"target is "
                f"{cls.SAFE_PROMPT_TOKENS}."
            )

            # Do not expose this to the user.
            # This is only a defensive fallback.
            prompt = (
                prompt[: int(
                    len(prompt)
                    * cls.SAFE_PROMPT_TOKENS
                    / estimated_tokens
                )]
                .rstrip()
            )

        return prompt