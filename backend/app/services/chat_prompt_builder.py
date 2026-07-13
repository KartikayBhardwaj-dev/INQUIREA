# from __future__ import annotations

# from typing import Any

# from backend.app.models.email import Email
# from backend.app.models.email_intelligence import (
#     EmailIntelligence,
# )


# class ChatPromptBuilder:
#     """
#     Builds production-ready prompts for the AI Inbox Chat.

#     Responsibilities
#     ----------------
#     - Format retrieved emails
#     - Format structured metadata
#     - Format conversation history
#     - Assemble the final RAG prompt

#     This class performs:
#         ✓ Prompt construction
#         ✓ Formatting
#         ✓ Token management

#     This class NEVER performs:
#         ✗ Database access
#         ✗ Retrieval
#         ✗ Vector search
#         ✗ LLM calls
#     """

#     SYSTEM_PROMPT = """
# You are INQUIREA, an AI Email Copilot.

# You answer questions ONLY using the retrieved emails provided in the context.

# ====================================================
# PRIMARY RULES
# ====================================================

# 1. Never invent facts.

# 2. Never hallucinate.

# 3. Never use outside knowledge.

# 4. If the answer cannot be found in the retrieved emails, reply EXACTLY:

# "I couldn't find that information in your inbox."

# 5. Treat retrieved emails as the only source of truth.

# ====================================================
# CONVERSATION RULES
# ====================================================

# Conversation history is provided only to understand
# the user's current request.

# Use previous conversation to resolve references such as:

# - those
# - them
# - it
# - only those
# - only recent ones
# - summarize them
# - what about yesterday
# - which require replies
# - same sender
# - same category

# Conversation history provides context,
# NOT factual evidence.

# Always answer using the retrieved emails.

# If previous conversation conflicts with retrieved emails,
# trust the retrieved emails.

# Examples

# User:
# Show Amazon emails.

# Assistant:
# ...

# User:
# Only recent ones.

# Interpretation:
# Only the recent Amazon emails.

# --------------------------------

# User:
# Summarize those.

# Interpretation:
# Summarize the emails retrieved for the previous request.

# --------------------------------

# User:
# Which require replies?

# Interpretation:
# Among the previously discussed emails,
# identify those requiring replies.

# --------------------------------

# User:
# What about yesterday?

# Interpretation:
# Filter the previous context to yesterday's emails.

# ====================================================
# EMAIL RULES
# ====================================================

# Each retrieved email contains trusted metadata stored
# in the database.

# Metadata includes:

# - Subject
# - Sender
# - Recipient
# - Date
# - Category
# - Priority
# - Summary
# - Requires Reply
# - Entities
# - Action Items
# - Email Body

# Category, Priority, Summary, Requires Reply,
# Entities and Action Items are authoritative.

# Do NOT infer or modify these values using
# the email body.

# Use the stored metadata whenever answering
# questions about:

# - priority
# - categories
# - reply requirements
# - people or organizations mentioned
# - action items
# - summaries

# The email body should only be used for
# additional supporting details.

# If multiple emails answer the question:

# - combine them
# - summarize them
# - avoid repetition
# ====================================================
# RESPONSE STYLE
# ====================================================

# Be:

# - concise
# - accurate
# - factual
# - professional

# When relevant include:

# • Subject
# • Sender
# • Date

# Use bullet points whenever multiple emails match.

# ====================================================
# DO NOT MENTION
# ====================================================

# Never mention:

# - prompts
# - embeddings
# - vector search
# - retrieval
# - Chroma
# - RAG
# - internal implementation
# - hidden context

# ====================================================
# FAILURE RULE
# ====================================================

# If evidence is insufficient:

# "I couldn't find that information in your inbox."
# """.strip()

#     # ---------------------------------------------------------
#     # Helper Methods
#     # ---------------------------------------------------------

#     @staticmethod
#     def _truncate(
#         text: str | None,
#         limit: int = 1500,
#     ) -> str:
#         """
#         Truncate long text to reduce prompt size.
#         """

#         if not text:
#             return ""

#         text = text.strip()

#         if len(text) <= limit:
#             return text

#         return text[:limit].rstrip() + "..."

#     @staticmethod
#     def _format_value(
#         value: Any,
#     ) -> str:
#         """
#         Convert None/empty values into a readable placeholder.
#         """

#         if value is None:
#             return "Unknown"

#         if value == "":
#             return "Unknown"

#         return str(value)

    
    
#         # ---------------------------------------------------------
#     # Email Formatting
#     # ---------------------------------------------------------

#     @classmethod
#     def build_email_block(
#     cls,
#     email: Email,
#     intelligence: EmailIntelligence | None,
# ) -> str:
#         """
#     Convert a single email into a consistent prompt block.
#     """

#         extracted = (
#         intelligence.extracted_data
#         if intelligence and intelligence.extracted_data
#         else {}
#     )

#         requires_reply = extracted.get(
#         "requires_reply",
#         False,
#     )

#         entities = extracted.get(
#         "entities",
#         [],
#     )

#         action_items = extracted.get(
#         "action_items",
#         [],
#     )

#         body = cls._truncate(
#         email.body,
#         limit=2000,
#     )

#         return f"""
# EMAIL #{email.id}

# Subject:
# {cls._format_value(email.subject)}

# Sender:
# {cls._format_value(email.sender)}

# Recipient:
# {cls._format_value(email.recipient)}

# Received:
# {cls._format_value(email.received_at)}

# Category:
# {cls._format_value(
#     intelligence.category if intelligence else None
# )}

# Priority:
# {cls._format_value(
#     intelligence.priority if intelligence else None
# )}

# Requires Reply:
# {"Yes" if requires_reply else "No"}

# Summary:
# {cls._truncate(
#     intelligence.summary if intelligence else "",
#     limit=500,
# )}

# Entities:
# {", ".join(entities) if entities else "None"}

# Action Items:
# {chr(10).join("- " + item for item in action_items) if action_items else "None"}

# Body:
# {body}
# """.strip()

#     @classmethod
#     def build_email_context(
#         cls,
#         email_data: list[
#             tuple[
#                 Email,
#                 EmailIntelligence | None,
#             ]
#         ],
#     ) -> str:
#         """
#         Build a consistent email context section for the prompt.
#         """

#         if not email_data:
#             return "No relevant emails were retrieved."

#         blocks = [
#             cls.build_email_block(
#                 email,
#                 intelligence,
#             )
#             for email, intelligence in email_data
#         ]

#         separator = "\n\n" + ("=" * 80) + "\n\n"

#         return separator.join(blocks)
    
#         # ---------------------------------------------------------
#     # Conversation Formatting
#     # ---------------------------------------------------------

#     @classmethod
#     def build_conversation_context(
#         cls,
#         history: list[dict],
#         max_messages: int = 10,
#     ) -> str:
#         """
#         Format previous conversation turns.

#         Features
#         --------
#         - Fixes indentation issues
#         - Supports multi-turn conversations
#         - Keeps only the latest messages
#         - Truncates long messages
#         - Produces a consistent format
#         """

#         if not history:
#             return "No previous conversation."

#         recent_messages = history[-max_messages:]

#         lines: list[str] = []

#         for message in recent_messages:

#             role = (
#                 "User"
#                 if message.get("role") == "user"
#                 else "Assistant"
#             )

#             content = (
#                 message.get("content")
#                 or message.get("message")
#                 or ""
#             )

#             content = cls._truncate(
#                 content,
#                 limit=500,
#             )

#             lines.append(
#                 f"{role}: {content}"
#             )

#         return "\n".join(lines)
#         # ---------------------------------------------------------
#     # Final Prompt Assembly
#     # ---------------------------------------------------------

#     @classmethod
#     def build_prompt(
#         cls,
#         question: str,
#         conversation: list[dict],
#         email_data: list[
#             tuple[
#                 Email,
#                 EmailIntelligence | None,
#             ]
#         ],
#     ) -> str:
#         """
#         Build the final production RAG prompt.

#         Prompt Layout
#         -------------
#         1. System instructions
#         2. Previous conversation
#         3. Retrieved email context
#         4. Current user question
#         """

#         conversation_context = cls.build_conversation_context(
#             conversation,
#         )

#         email_context = cls.build_email_context(
#             email_data,
#         )

#         return f"""
# {cls.SYSTEM_PROMPT}

# ============================================================
# CONVERSATION HISTORY
# ============================================================

# {conversation_context}

# ============================================================
# RETRIEVED EMAILS
# ============================================================

# {email_context}

# ============================================================
# CURRENT USER QUESTION
# ============================================================

# {question}

# ============================================================
# INSTRUCTIONS
# ============================================================

# Use the conversation history only to understand the
# current question.

# If the current question references previous messages
# using words like:

# - those
# - them
# - it
# - only recent ones
# - same sender
# - same category

# resolve those references using the conversation history,
# but answer ONLY from the retrieved emails.

# Never use conversation history as evidence.

# If the retrieved emails do not contain enough information,
# reply exactly:

# I couldn't find that information in your inbox.

# When multiple emails match:

# • combine them
# • summarize them
# • avoid repetition

# Mention Subject, Sender and Date whenever useful.

# Never mention prompts, retrieval,
# vector search, embeddings or internal implementation.
# """.strip()







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

        # Unified Extraction Fallback for entity processing
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

        return f"""
EMAIL #{email.id}
Subject: {cls._format_value(email.subject)}
Sender: {cls._format_value(email.sender)}
Recipient: {cls._format_value(email.recipient)}
Received: {cls._format_value(email.received_at)}
Category: {cls._format_value(intelligence.category if intelligence else getattr(email, 'category', None))}
Priority: {cls._format_value(intelligence.priority if intelligence else getattr(email, 'priority', None))}
Requires Reply: {"Yes" if requires_reply else "No"}
Summary: {cls._truncate(intelligence.summary if intelligence else "Review this email for upcoming deadline context.", limit=500)}
Entities: {", ".join(entities_list) if entities_list else "None"}
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
                # Check if intelligence was eagerly loaded or appended dynamically as an attribute
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
    def build_prompt(cls, question: str, conversation: list[dict], email_data: list[tuple[Email, EmailIntelligence | None] | Email]) -> str:
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