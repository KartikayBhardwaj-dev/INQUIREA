from __future__ import annotations

import logging
import re
from typing import Any, Literal

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, ConfigDict, Field

from backend.app.core.config import EmailCategory
from backend.app.core.llm import get_llm

logger = logging.getLogger(__name__)


class QueryPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    intent: Literal[
        "semantic_search",
        "summarize",
        "sender_lookup",
        "deadline_search",
        "metadata_search",
    ]

    semantic_query: str | None = None
    email_reference: str | None = None
    category: str | None = None

    priority: Literal[
        "low",
        "medium",
        "high",
        "urgent",
    ] | None = None

    sender: str | None = None

    requires_reply: bool | None = None

    retrieve_limit: int = Field(
        default=5,
        ge=1,
        le=50,
    )

    sort_by: Literal[
        "relevance",
        "date",
        "priority",
    ] = "relevance"

    date_from: str | None = None
    date_to: str | None = None

    reasoning: str = ""

    needs_tool: bool = False

    tool_name: str | None = None

    tool_arguments: dict[str, Any] = Field(
        default_factory=dict,
    )

    needs_clarification: bool = False

    clarification_message: str | None = None


class QueryPlanner:

    def __init__(self):

        self.parser = PydanticOutputParser(
        pydantic_object=QueryPlan
    )

        categories_list = ", ".join(
        c.value for c in EmailCategory
    )

        system_prompt = """
You are the Retrieval Planning Engine for INQUIREA.

Your job is ONLY to convert a user's request into a
structured QueryPlan.

You do not answer the user.
You do not summarize emails.
You do not execute tools.
You never invent IDs.

Choose exactly one intent:

- semantic_search
- summarize
- metadata_search
- sender_lookup
- deadline_search

========================================================
SEARCH INTERPRETATION
========================================================

Use semantic_search for natural-language requests about
email content, topics, products, offers, people, events,
or concepts.

Examples:

"Show me promotional emails"
"Find emails about student discounts"
"Show marketing emails about student deals"
"Find emails mentioning internships"
"Which emails talk about discounts?"

Use metadata_search when the user explicitly asks for
structured email metadata such as category, priority,
reply requirement, or similar fields.

Use sender_lookup when the request is primarily about
emails from a particular sender.

Use deadline_search when the request is primarily about
deadlines, due dates, or time-sensitive tasks.

Use summarize when the user explicitly asks to summarize
one or more emails or a group of emails.

========================================================
SEMANTIC QUERY
========================================================

For semantic_search, preserve the important meaning of
the user's request in semantic_query.

Example:

User:
Show me promotional or marketing emails about student deals

Use:

semantic_query =
"promotional or marketing emails about student deals"

Do not replace the user's topic with a generic query.

========================================================
EMAIL REFERENCES
========================================================

If the user refers to an email by a natural-language
subject or title, preserve it in email_reference.

Never invent an email_id.

========================================================
CONVERSATIONAL CONTEXT
========================================================

Conversation history may contain small structured
metadata from previous actions.

Relevant fields include:

- email_id
- draft_id
- tool
- action

When an existing email or draft is referenced as:

- it
- this email
- that email
- this draft
- that draft

use the most recent relevant structured ID.

An explicit ID in the current user message always
overrides previous context.

Never invent IDs.

========================================================
RETRIEVAL SETTINGS
========================================================

Default retrieve_limit = 5.

Use up to 50 when necessary.

Use sort_by = relevance by default.

Use sort_by = date for requests such as:

- latest
- newest
- recent
- most recent

Use sort_by = priority when the user explicitly asks
for highest-priority emails.

For summarize, retrieve_limit should normally be 20.

For sender_lookup and deadline_search, retrieve_limit
should normally be 10.

========================================================
FILTERS
========================================================

Valid categories:

__CATEGORIES_LIST__

Use category only when the request clearly specifies
a known email category.

Valid priorities:

- low
- medium
- high
- urgent

Use priority only when explicitly requested.

Use requires_reply only when the user explicitly asks
about emails that require or do not require a reply.

Use sender only when a sender is explicitly identified.

Use date_from and date_to only for explicit date filters.

Keep natural-language date context in semantic_query.

========================================================
OUTPUT
========================================================

Return ONLY valid JSON matching QueryPlan.

tool_arguments must be an object.

reasoning must always be present.

{format_instructions}
"""

        system_prompt = system_prompt.replace(
        "__CATEGORIES_LIST__",
        categories_list,
    )

        self.prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            (
                "user",
                "Conversation History:\n"
                "{conversation_history}\n\n"
                "Current Question:\n"
                "{question}",
            ),
        ]
    )

    # ======================================================
    # STRUCTURED CONTEXT EXTRACTION
    # ======================================================

    @staticmethod
    def _get_context_ids(
        conversation: list[dict[str, Any]],
    ) -> dict[str, Any]:

        """
        Extract the most recent draft and email context
        independently.

        Draft context and email context are intentionally
        tracked separately because a later email-related
        action should not accidentally replace the current
        draft reference.
        """

        context: dict[str, Any] = {
            "tool": None,
            "draft_id": None,
            "email_id": None,
        }

        for message in reversed(conversation):

            metadata = message.get("metadata")

            if not isinstance(metadata, dict):
                continue

            if context["draft_id"] is None:

                draft_id = metadata.get("draft_id")

                if draft_id is not None:
                    context["draft_id"] = draft_id

            if context["email_id"] is None:

                email_id = metadata.get("email_id")

                if email_id is not None:
                    context["email_id"] = email_id

            if context["tool"] is None:

                tool = (
                    metadata.get("tool")
                    or metadata.get("action")
                )

                if tool is not None:
                    context["tool"] = tool

            if (
                context["draft_id"] is not None
                and context["email_id"] is not None
                and context["tool"] is not None
            ):
                break

        return context

    def _extract_email_reference(
        self,
        question: str,
    ) -> str | None:

        match = re.search(
            r'\bemail\b'
            r'(?:\s+(?:titled|called|named))?'
            r'\s*["\']([^"\']+)["\']',
            question,
            re.IGNORECASE,
        )

        if match:
            return match.group(1).strip()

        return None

    def _detect_generate_reply_action(
        self,
        question: str,
        email_reference: str | None,
        context: dict[str, Any],
        explicit_ids: dict[str, int],
    ) -> tuple[str | None, dict[str, Any]]:

        """
        Deterministically detect requests to generate a reply.

        Supports:

        - Generate a reply to email 10
        - Generate a reply to the email "4 new image styles to try"
        - Write a reply to this email
        - Draft a response to this email
        """

        lowered = question.strip().lower()

        generate_patterns = (
            r"\bgenerate\b.*\breply\b",
            r"\bwrite\b.*\breply\b",
            r"\bdraft\b.*\breply\b",
            r"\bcreate\b.*\breply\b",
            r"\bcompose\b.*\breply\b",
            r"\bwrite\b.*\bresponse\b",
            r"\bdraft\b.*\bresponse\b",
            r"\bcreate\b.*\bresponse\b",
            r"\bcompose\b.*\bresponse\b",
        )

        if not any(
            re.search(pattern, lowered)
            for pattern in generate_patterns
        ):
            return None, {}

        arguments: dict[str, Any] = {}

        # Explicit email ID has highest priority.
        if explicit_ids.get("email_id") is not None:

            arguments["email_id"] = (
                explicit_ids["email_id"]
            )

        # Natural-language subject/reference.
        elif email_reference:

            arguments["email_reference"] = (
                email_reference
            )

        # Otherwise use the most recent email context.
        elif context.get("email_id") is not None:

            arguments["email_id"] = (
                context["email_id"]
            )

        else:

            return None, {}

        arguments["tone"] = "professional"

        return "generate_reply", arguments

    # ======================================================
    # EXPLICIT ID EXTRACTION
    # ======================================================

    @staticmethod
    def _extract_explicit_ids(
        question: str,
    ) -> dict[str, int]:

        ids: dict[str, int] = {}

        draft_match = re.search(
            r"\bdraft(?:_reply_id)?\s*(?:#|id)?\s*(\d+)",
            question,
            re.IGNORECASE,
        )

        email_match = re.search(
            r"\bemail\s*(?:#|id)?\s*(\d+)",
            question,
            re.IGNORECASE,
        )

        if draft_match:

            ids["draft_id"] = int(
                draft_match.group(1)
            )

        if email_match:

            ids["email_id"] = int(
                email_match.group(1)
            )

        return ids

    # ======================================================
    # DRAFT ACTION DETECTION
    # ======================================================

    @staticmethod
    def _detect_draft_action(
        question: str,
        context: dict[str, Any],
    ) -> tuple[str | None, dict[str, Any]]:

        """
        Deterministically detect common conversational
        actions against the current draft.

        This protects the draft workflow from LLM planning
        ambiguity.
        """

        draft_id = context.get("draft_id")

        if draft_id is None:
            return None, {}

        text = question.strip()
        lowered = text.lower()

        # --------------------------------------------------
        # APPROVE
        # --------------------------------------------------

        if re.search(
            r"\b(approve|approved)\b",
            lowered,
        ):

            return (
                "approve_draft",
                {
                    "draft_id": draft_id,
                },
            )

        # --------------------------------------------------
        # REJECT
        # --------------------------------------------------

        if re.search(
            r"\b(reject|rejected|discard)\b",
            lowered,
        ):

            return (
                "reject_draft",
                {
                    "draft_id": draft_id,
                },
            )

        # --------------------------------------------------
        # SEND
        # --------------------------------------------------

        if re.search(
            r"\b(send|send it|send this)\b",
            lowered,
        ):

            return (
                "send_reply",
                {
                    "draft_id": draft_id,
                },
            )

        # --------------------------------------------------
        # REGENERATE
        # --------------------------------------------------

        if re.search(
            r"\b(regenerate|generate again|try again)\b",
            lowered,
        ):

            return (
                "rewrite_reply",
                {
                    "draft_id": draft_id,
                    "instruction": (
                        "Regenerate the draft while preserving "
                        "the original intent and important "
                        "information."
                    ),
                },
            )

        # --------------------------------------------------
        # REWRITE / MODIFY
        # --------------------------------------------------

        rewrite_patterns = (
            r"\bmake\b",
            r"\bchange\b",
            r"\bremove\b",
            r"\badd\b",
            r"\binclude\b",
            r"\bshorten\b",
            r"\bexpand\b",
            r"\brewrite\b",
            r"\bmodify\b",
            r"\bimprove\b",
            r"\bfix\b",
            r"\bturn\b",
            r"\bconvert\b",
            r"\bmake it\b",
            r"\bmake this\b",
        )

        if any(
            re.search(pattern, lowered)
            for pattern in rewrite_patterns
        ):

            return (
                "rewrite_reply",
                {
                    "draft_id": draft_id,
                    "instruction": text,
                },
            )

        return None, {}

    # ======================================================
    # PLAN
    # ======================================================

    async def plan(
        self,
        question: str,
        conversation: list[dict[str, Any]] | None = None,
    ) -> QueryPlan:

        conversation = conversation or []

        # ==================================================
        # 1. EXTRACT CONVERSATIONAL CONTEXT
        # ==================================================

        context = self._get_context_ids(
            conversation
        )

        explicit_ids = self._extract_explicit_ids(
            question
        )

        email_reference = self._extract_email_reference(
            question
        )

        logger.debug(
            "Planner context: %s",
            context,
        )

        logger.debug(
            "Explicit IDs: %s",
            explicit_ids,
        )

        # ==================================================
        # 2. DETERMINISTIC ACTION DETECTION
        # ==================================================

        generate_action, generate_action_arguments = (
            self._detect_generate_reply_action(
                question=question,
                email_reference=email_reference,
                context=context,
                explicit_ids=explicit_ids,
            )
        )

        logger.debug(
            "Detected generate reply action: %s %s",
            generate_action,
            generate_action_arguments,
        )

        draft_action, draft_action_arguments = (
            self._detect_draft_action(
                question=question,
                context=context,
            )
        )

        # Generate-reply is special because there is no
        # draft_id before the first draft is created.
        if generate_action:

            draft_action = generate_action

            draft_action_arguments = (
                generate_action_arguments
            )

        logger.debug(
            "Detected draft action: %s %s",
            draft_action,
            draft_action_arguments,
        )

        # ==================================================
        # 3. DETERMINISTIC ACTION SHORT-CIRCUIT
        # ==================================================
        #
        # IMPORTANT:
        #
        # If an action has already been identified
        # deterministically, DO NOT call the LLM planner.
        #
        # This prevents:
        #
        #   action request
        #       ↓
        #   huge LLM request
        #       ↓
        #   Groq 413 / rate limit
        #       ↓
        #   semantic-search fallback
        #
        # It also guarantees that actions such as
        # generate_reply, approve_draft, reject_draft,
        # send_reply, and rewrite_reply are not converted
        # into ordinary retrieval requests because of an
        # unrelated LLM failure.
        # ==================================================

        if draft_action:

            plan = QueryPlan(
                intent="semantic_search",
                semantic_query=question,
                email_reference=email_reference,
                reasoning=(
                    "Deterministic action detected; "
                    "LLM planning bypassed."
                ),
                needs_tool=True,
                tool_name=draft_action,
                tool_arguments=dict(
                    draft_action_arguments
                ),
            )

            logger.debug(
                "Using deterministic action plan "
                "without LLM: %s",
                plan.model_dump(),
            )

        else:

            # ==================================================
            # 4. BUILD HISTORY
            # ==================================================
            
            # ==================================================
# 4. BUILD COMPACT HISTORY
# ==================================================

            history_str = "No previous conversation history."

            if conversation:

                history_parts: list[str] = []

    # Only the most recent few messages are useful for
    # resolving conversational context.
                recent_messages = conversation[-6:]

                for message in recent_messages:

                    role = message.get(
            "role",
            "user",
        )

                    content = message.get(
            "message",
            message.get(
                "content",
                "",
            ),
        )

        # Prevent huge assistant responses from entering
        # the planner prompt.
                    if content:

                        content = str(content).strip()

                        if len(content) > 1000:

                            content = content[:1000] + "..."

                    history_parts.append(
            f"{str(role).capitalize()}: {content}"
        )

                    metadata = message.get(
            "metadata",
            {},
        )

        # Only pass the small structured fields that
        # actually matter for planning.
                    if isinstance(metadata, dict):

                        compact_metadata = {}

                        for key in (
                "tool",
                "action",
                "email_id",
                "draft_id",
            ):  
                            

                            value = metadata.get(key)

                            if value is not None:

                                compact_metadata[key] = value

                        if compact_metadata:

                            history_parts.append(
                    "Structured metadata: "
                    f"{compact_metadata}"
                )

                history_str = "\n".join(
        history_parts
    )

            # ==================================================
            # 5. CALL LLM
            # ==================================================

            llm_instance = get_llm()

            chain = (
                self.prompt.partial(
                    format_instructions=(
                        self.parser.get_format_instructions()
                    )
                )
                | llm_instance
                | self.parser
            )

            try:

                plan: QueryPlan = await chain.ainvoke(
                    {
                        "question": question,
                        "conversation_history": history_str,
                    }
                )

            except Exception:

                logger.exception(
                    "Failed to parse QueryPlan."
                )

                return QueryPlan(
                    intent="semantic_search",
                    semantic_query=question,
                    reasoning=(
                        "Planner LLM failed. "
                        "No deterministic action was detected."
                    ),
                )

        # ==================================================
        # 6. BASIC NORMALIZATION
        # ==================================================

        plan.reasoning = (
            plan.reasoning or ""
        )

        plan.tool_arguments = (
            plan.tool_arguments or {}
        )

        # --------------------------------------------------
        # Natural-language email reference
        # --------------------------------------------------

        if email_reference:

            plan.email_reference = (
                email_reference
            )

            plan.tool_arguments[
                "email_reference"
            ] = email_reference

        # ==================================================
        # 7. SEMANTIC NORMALIZATION
        # ==================================================

        if not plan.semantic_query:

            plan.semantic_query = question

        else:

            plan.semantic_query = (
                plan.semantic_query.strip()
            )

        if plan.priority:

            plan.priority = (
                plan.priority.lower().strip()
            )

            if plan.priority not in {
                "low",
                "medium",
                "high",
                "urgent",
            }:

                plan.priority = None

        if plan.category:

            plan.category = (
                plan.category.strip().lower()
            )

            if plan.category not in {
                c.value
                for c in EmailCategory
            }:

                plan.category = None

        if plan.sender:

            plan.sender = (
                plan.sender.strip()
            )

        if plan.date_from:

            plan.date_from = (
                plan.date_from.strip()
            )

        if plan.date_to:

            plan.date_to = (
                plan.date_to.strip()
            )

        plan.retrieve_limit = max(
            1,
            min(
                plan.retrieve_limit,
                50,
            ),
        )

        if plan.sort_by not in {
            "relevance",
            "date",
            "priority",
        }:

            plan.sort_by = "relevance"

        if (
            plan.intent == "summarize"
            and plan.retrieve_limit < 20
        ):

            plan.retrieve_limit = 20

        if (
            plan.intent == "deadline_search"
            and plan.sort_by != "date"
        ):

            plan.sort_by = "date"

        # ==================================================
        # 8. VALIDATE / NORMALIZE TOOL
        # ==================================================

        valid_tools = {
            "search_emails",
            "get_email",
            "generate_reply",
            "rewrite_reply",
            "edit_draft",
            "approve_draft",
            "reject_draft",
            "save_draft",
            "update_draft",
            "send_reply",
        }

        if plan.tool_name:

            plan.tool_name = (
                plan.tool_name.strip().lower()
            )

        if plan.tool_name not in valid_tools:

            if plan.needs_tool:

                plan.needs_tool = False
                plan.tool_name = None
                plan.tool_arguments = {}

        # ==================================================
        # 9. RESOLVE IDS
        #
        # Explicit current-message IDs ALWAYS win.
        # ==================================================

        for key, value in explicit_ids.items():

            plan.tool_arguments[key] = value

        # --------------------------------------------------
        # Draft context
        # --------------------------------------------------

        if (
            "draft_id" not in plan.tool_arguments
            and context.get("draft_id") is not None
        ):

            plan.tool_arguments["draft_id"] = (
                context["draft_id"]
            )

        # --------------------------------------------------
        # Email context
        # --------------------------------------------------

        if (
            "email_id" not in plan.tool_arguments
            and context.get("email_id") is not None
        ):

            plan.tool_arguments["email_id"] = (
                context["email_id"]
            )

        # ==================================================
        # 10. NORMALIZE IDS
        #
        # IMPORTANT:
        # This happens BEFORE required validation.
        # ==================================================

        for key in (
            "email_id",
            "draft_id",
        ):

            value = plan.tool_arguments.get(
                key
            )

            if value is None:
                continue

            # bool must not be accepted as an integer ID.
            if isinstance(value, bool):

                plan.tool_arguments.pop(
                    key,
                    None,
                )

                continue

            if isinstance(value, int):

                if value <= 0:

                    plan.tool_arguments.pop(
                        key,
                        None,
                    )

                continue

            if isinstance(value, str):

                value = value.strip()

                match = re.search(
                    r"\d+",
                    value,
                )

                if match:

                    normalized_id = int(
                        match.group()
                    )

                    if normalized_id > 0:

                        plan.tool_arguments[
                            key
                        ] = normalized_id

                    else:

                        plan.tool_arguments.pop(
                            key,
                            None,
                        )

                else:

                    plan.tool_arguments.pop(
                        key,
                        None,
                    )

            else:

                plan.tool_arguments.pop(
                    key,
                    None,
                )

        # ==================================================
        # 11. NORMALIZE TONE
        # ==================================================

        if plan.tool_name == "generate_reply":

            tone = plan.tool_arguments.get(
                "tone"
            )

            if tone is None:

                tone = "professional"

            else:

                tone = (
                    str(tone)
                    .strip()
                    .lower()
                )

                if not tone:

                    tone = "professional"

            plan.tool_arguments["tone"] = tone

        # ==================================================
        # 12. NORMALIZE REWRITE INSTRUCTION
        # ==================================================

        if plan.tool_name == "rewrite_reply":

            instruction = (
                plan.tool_arguments.get(
                    "instruction"
                )
            )

            if instruction is not None:

                instruction = str(
                    instruction
                ).strip()

            # If LLM did not provide instruction,
            # current user request becomes the instruction.
            if not instruction:

                instruction = question.strip()

            if instruction:

                plan.tool_arguments[
                    "instruction"
                ] = instruction

            else:

                plan.tool_arguments.pop(
                    "instruction",
                    None,
                )

        # ==================================================
        # 13. REQUIRED ARGUMENTS
        # ==================================================

        required_tool_arguments = {

            "send_reply": [
                "draft_id",
            ],

            "update_draft": [
                "draft_id",
            ],

            "save_draft": [
                "draft_id",
            ],

            "approve_draft": [
                "draft_id",
            ],

            "reject_draft": [
                "draft_id",
            ],

            "get_email": [
                "email_id",
            ],

            "generate_reply": [
                "email_id",
            ],

            "rewrite_reply": [
                "draft_id",
                "instruction",
            ],

            "edit_draft": [
                "draft_id",
                "content",
            ],
        }

        # ==================================================
        # 14. VALIDATE REQUIRED ARGUMENTS
        # ==================================================

        if plan.needs_tool:

            required = (
                required_tool_arguments.get(
                    plan.tool_name,
                    [],
                )
            )

            missing: list[str] = []

            for argument in required:

                value = (
                    plan.tool_arguments.get(
                        argument
                    )
                )

                # --------------------------------------------------
                # generate_reply special case
                # --------------------------------------------------
                #
                # A generate_reply request can provide either:
                #
                #   email_id
                #
                # OR:
                #
                #   email_reference
                #
                # The ChatAgent resolves
                # email_reference -> email_id.
                #
                # Therefore the planner MUST NOT ask the user
                # for email_id when an email_reference is available.
                # --------------------------------------------------

                if (
                    plan.tool_name == "generate_reply"
                    and argument == "email_id"
                    and plan.tool_arguments.get(
                        "email_reference"
                    )
                ):

                    continue

                if value is None:

                    missing.append(argument)

                    continue

                if (
                    isinstance(value, str)
                    and not value.strip()
                ):

                    missing.append(argument)

            # ==================================================
            # 15. CLARIFICATION
            # ==================================================

            if missing:

                plan.needs_clarification = True

                if (
                    plan.tool_name
                    == "rewrite_reply"
                ):

                    if "draft_id" in missing:

                        plan.clarification_message = (
                            "I need a draft ID to rewrite. "
                            "Please specify the draft or "
                            "tell me which draft you mean."
                        )

                    else:

                        plan.clarification_message = (
                            "What would you like me to "
                            "change in the draft?"
                        )

                elif (
                    plan.tool_name
                    == "edit_draft"
                ):

                    plan.clarification_message = (
                        "I need the draft ID and "
                        "the new draft content."
                    )

                else:

                    plan.clarification_message = (
                        "Missing required information: "
                        + ", ".join(missing)
                        + "."
                    )

                # Never execute an incomplete tool call.
                plan.needs_tool = False
                plan.tool_name = None
                plan.tool_arguments = {}

        # ==================================================
        # 16. FINAL LOGGING
        # ==================================================

        logger.debug(
            "Final normalized QueryPlan: %s",
            plan.model_dump(),
        )

        return plan