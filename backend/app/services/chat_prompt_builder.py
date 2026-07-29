from __future__ import annotations

from typing import Any
from backend.app.models.email import Email
from backend.app.models.email_intelligence import EmailIntelligence


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
Always answer using the retrieved emails. Never use conversation history as evidence.

====================================================
EMAIL RULES
====================================================
Use the stored metadata whenever answering questions about priority, categories, summaries, entities, or actions.
If specific pieces of information (like exact dates or deadlines) are mentioned in the email summaries, body text, or subjects, summarize those details clearly for the user.

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
RESPONSE STYLE & RULES
====================================================
Be concise, accurate, and professional. Mention Subject, Sender, and Date where useful.
Never mention internal configurations, vector stores, prompts, or engineering internals.
""".strip()

    @staticmethod
    def _truncate(text: str | None, limit: int = 1500) -> str:
        if not text:
            return ""
        text = text.strip()
        return text if len(text) <= limit else text[:limit].rstrip() + "..."

    @staticmethod
    def _format_value(value: Any) -> str:
        return "Unknown" if value in (None, "") else str(value)

    @classmethod
    def build_email_block(cls, email: Email, intelligence: EmailIntelligence | None) -> str:
        extracted = intelligence.extracted_data if intelligence and intelligence.extracted_data else {}
        requires_reply = extracted.get("requires_reply", False)

        entities_raw = extracted.get("extracted_entities", extracted.get("entities", {}))

        entities_list = []
        action_items = []

        if isinstance(entities_raw, dict):
            action_items = entities_raw.get("action_items", [])
            for k, v in entities_raw.items():
                if k != "action_items" and isinstance(v, list):
                    entities_list.extend(v)
        elif isinstance(entities_raw, list):
            entities_list = entities_raw

        body = cls._truncate(email.body, limit=2000)

        category = intelligence.category if intelligence and intelligence.category else getattr(email, "category", None)
        priority = intelligence.priority if intelligence and intelligence.priority else getattr(email, "priority", None)
        summary = intelligence.summary if intelligence and intelligence.summary else "Review this email for upcoming context."

        return f"""
EMAIL #{email.id}
Subject: {cls._format_value(email.subject)}
Sender: {cls._format_value(email.sender)}
Recipient: {cls._format_value(email.recipient)}
Received: {cls._format_value(email.received_at)}
Category: {cls._format_value(category)}
Priority: {cls._format_value(priority)}
Requires Reply: {"Yes" if requires_reply else "No"}
Summary: {cls._truncate(summary, limit=500)}
Entities: {", ".join(str(e) for e in entities_list) if entities_list else "None"}
Action Items:
{chr(10).join("- " + str(item) for item in action_items) if action_items else "None"}
Body:
{body}
""".strip()

    @classmethod
    def build_email_context(cls, email_data: list[tuple[Email, EmailIntelligence | None] | Email]) -> str:
        if not email_data:
            return "No relevant emails were retrieved."

        blocks = []
        for item in email_data:
            if isinstance(item, tuple):
                email, intelligence = item
            else:
                email = item
                intelligence = getattr(email, "intelligence", None)

            blocks.append(cls.build_email_block(email, intelligence))

        return ("\n\n" + ("=" * 80) + "\n\n").join(blocks)

    @classmethod
    def build_conversation_context(cls, history: list[dict], max_messages: int = 10) -> str:
        if not history:
            return "No previous conversation."
        recent_messages = history[-max_messages:]
        lines: list[str] = []
        for message in recent_messages:
            role = "User" if message.get("role") == "user" else "Assistant"
            content = message.get("content") or message.get("message") or ""
            lines.append(f"{role}: {cls._truncate(content, limit=500)}")
        return "\n".join(lines)

    @classmethod
    def build_prompt(
        cls,
        question: str,
        conversation: list[dict],
        email_data: list[tuple[Email, EmailIntelligence | None] | Email],
    ) -> str:
        return f"""
{cls.SYSTEM_PROMPT}

============================================================
CONVERSATION HISTORY
============================================================
{cls.build_conversation_context(conversation)}

============================================================
RETRIEVED EMAILS
============================================================
{cls.build_email_context(email_data)}

============================================================
CURRENT USER QUESTION
============================================================
{question}
""".strip()