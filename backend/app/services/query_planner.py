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

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"""
You are the Retrieval Planning Engine for INQUIREA.

Your ONLY responsibility is to transform the user's request
into a structured QueryPlan.

You NEVER answer the user.
You NEVER summarize emails.
You NEVER invent IDs.

Return ONLY valid JSON matching QueryPlan.

========================================================
AVAILABLE INTENTS
========================================================

1. semantic_search
2. summarize
3. metadata_search
4. sender_lookup
5. deadline_search

Choose exactly ONE.

========================================================
STRUCTURED CONVERSATION CONTEXT
========================================================

Conversation history may contain structured metadata.

Example:

{{
    "role": "assistant",
    "message": "Draft generated.",
    "metadata": {{
        "tool": "generate_reply",
        "draft_id": 15,
        "email_id": 10
    }}
}}

Use this structured metadata to resolve:

- it
- this draft
- that draft
- this email
- make it shorter
- make it professional
- make it friendlier
- approve it
- reject it
- save it
- send it

NEVER invent IDs.

If an explicit ID is present in the current user request,
prefer that ID.

Otherwise use the most recent relevant structured metadata.

========================================================
LEVEL 2 TOOLS
========================================================

Available tools:

- search_emails
- get_email
- generate_reply
- rewrite_reply
- edit_draft
- approve_draft
- reject_draft
- save_draft
- update_draft
- send_reply

Use a tool when the user wants an ACTION.

========================================================
GENERATE REPLY
========================================================

"Generate a reply to email 10"

{{
    "needs_tool": true,
    "tool_name": "generate_reply",
    "tool_arguments": {{
        "email_id": 10,
        "tone": "professional"
    }}
}}

========================================================
REWRITE REPLY
========================================================

rewrite_reply requires:

- draft_id
- instruction

The instruction is NOT the same thing as tone.

Examples:

"Make it shorter"

{{
    "draft_id": 15,
    "instruction": "make it shorter"
}}

"Make it more professional"

{{
    "draft_id": 15,
    "instruction": "make it more professional"
}}

"Change the ending"

{{
    "draft_id": 15,
    "instruction": "change the ending"
}}

"Remove unnecessary details"

{{
    "draft_id": 15,
    "instruction": "remove unnecessary details"
}}

========================================================
EDIT DRAFT
========================================================

Only use edit_draft when the user explicitly supplies
replacement content.

It requires:

draft_id
content

========================================================
APPROVE
========================================================

"Approve draft 15"

{{
    "draft_id": 15
}}

"Approve it"

Use the draft_id from structured conversation metadata.

========================================================
REJECT
========================================================

"Reject draft 15"

{{
    "draft_id": 15
}}

"Reject it"

Use the draft_id from structured conversation metadata.

========================================================
SAVE
========================================================

"Save draft 15"

{{
    "draft_id": 15
}}

"Save it"

Use structured conversation metadata.

========================================================
UPDATE
========================================================

"Update draft 15"

{{
    "draft_id": 15
}}

========================================================
SEND
========================================================

"Send draft 15"

{{
    "draft_id": 15
}}

"Send it"

Use structured conversation metadata.

========================================================
ID RULE
========================================================

Priority:

1. Current user message
2. Structured conversation metadata
3. No ID

If no ID can be resolved:

needs_clarification = true

Do not invent an ID.

========================================================
GENERATE REPLY TONE
========================================================

generate_reply defaults to:

"professional"

========================================================
REWRITE INSTRUCTION
========================================================

rewrite_reply MUST contain:

"instruction"

Do not reduce instructions to a tone.

Examples:

"make it shorter"
"make it professional"
"make it friendlier"
"change the ending"
"remove unnecessary details"
"make it concise"

========================================================
CATEGORY
========================================================

Valid categories:

{categories_list}

========================================================
RETRIEVAL
========================================================

Default limit = 5.

Summarize = 20.

Sender/deadline = 10.

Maximum = 50.

Default sort = relevance.

Latest/recent = date.

Highest priority = priority.

========================================================
DATE RULE
========================================================

Only use date_from/date_to for explicit date filters.

Keep contextual dates inside semantic_query.

========================================================
OUTPUT
========================================================

Return ONLY valid JSON.

Do not create fields outside QueryPlan.

tool_arguments must always be an object.

reasoning must always be present.

{{
format_instructions
}}
""",
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

    # ------------------------------------------------------
    # Structured context extraction
    # ------------------------------------------------------

    @staticmethod
    def _get_context_ids(
        conversation: list[dict[str, Any]],
    ) -> dict[str, Any]:

        context: dict[str, Any] = {}

        for message in reversed(conversation):

            metadata = message.get("metadata")

            if not isinstance(metadata, dict):
                continue

            if (
                "draft_id" not in context
                and metadata.get("draft_id") is not None
            ):
                context["draft_id"] = metadata["draft_id"]

            if (
                "email_id" not in context
                and metadata.get("email_id") is not None
            ):
                context["email_id"] = metadata["email_id"]

            if (
                "tool" not in context
                and metadata.get("tool")
            ):
                context["tool"] = metadata["tool"]

            # We have enough context.
            if (
                "draft_id" in context
                and "email_id" in context
                and "tool" in context
            ):
                break

        return context

    # ------------------------------------------------------
    # Explicit ID extraction
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # Plan
    # ------------------------------------------------------

    async def plan(
        self,
        question: str,
        conversation: list[dict[str, Any]] | None = None,
    ) -> QueryPlan:

        conversation = conversation or []

        context = self._get_context_ids(
            conversation
        )

        explicit_ids = self._extract_explicit_ids(
            question
        )

        history_str = (
            "No previous conversation history."
        )

        if conversation:

            history_parts = []

            for message in conversation:

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

                metadata = message.get(
                    "metadata",
                    {},
                )

                history_parts.append(
                    f"{str(role).capitalize()}: "
                    f"{content}"
                )

                if metadata:
                    history_parts.append(
                        "Structured metadata: "
                        f"{metadata}"
                    )

            history_str = "\n".join(
                history_parts
            )

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
                    "Fallback retrieval plan generated "
                    "after planner failure."
                ),
            )

        plan.reasoning = (
            plan.reasoning or ""
        )

        plan.tool_arguments = (
            plan.tool_arguments or {}
        )

        # --------------------------------------------------
        # Normalize semantic fields
        # --------------------------------------------------

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

            if plan.category not in [
                c.value
                for c in EmailCategory
            ]:
                plan.category = None

        if plan.sender:
            plan.sender = plan.sender.strip()

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

        # --------------------------------------------------
        # Normalize tool
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Deterministically resolve IDs
        # --------------------------------------------------

        # Current user IDs always win.
        for key, value in explicit_ids.items():

            plan.tool_arguments[key] = value

        # If current message did not contain an ID,
        # recover it from structured conversation metadata.
        if (
            "draft_id"
            not in plan.tool_arguments
            and context.get("draft_id") is not None
        ):
            plan.tool_arguments["draft_id"] = (
                context["draft_id"]
            )

        if (
            "email_id"
            not in plan.tool_arguments
            and context.get("email_id") is not None
        ):
            plan.tool_arguments["email_id"] = (
                context["email_id"]
            )

        # --------------------------------------------------
        # Normalize ID types
        # --------------------------------------------------

        for key in (
            "email_id",
            "draft_id",
        ):

            value = plan.tool_arguments.get(
                key
            )

            if isinstance(value, int):
                continue

            if isinstance(value, str):

                match = re.search(
                    r"\d+",
                    value,
                )

                if match:
                    plan.tool_arguments[key] = int(
                        match.group()
                    )

        # --------------------------------------------------
        # Infer rewrite instruction
        # --------------------------------------------------

        if plan.tool_name == "rewrite_reply":

            instruction = (
                plan.tool_arguments.get(
                    "instruction"
                )
            )

            if instruction is None:

                # Recover instruction from current user
                # request when the LLM omitted it.
                normalized_question = (
                    question.strip()
                )

                if normalized_question:
                    plan.tool_arguments[
                        "instruction"
                    ] = normalized_question

            else:

                instruction = str(
                    instruction
                ).strip()

                if instruction:

                    plan.tool_arguments[
                        "instruction"
                    ] = instruction

                else:

                    plan.tool_arguments[
                        "instruction"
                    ] = question.strip()

        # --------------------------------------------------
        # Generate reply default tone
        # --------------------------------------------------

        if plan.tool_name == "generate_reply":

            plan.tool_arguments.setdefault(
                "tone",
                "professional",
            )

        # --------------------------------------------------
        # Required arguments
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Validate tool
        # --------------------------------------------------

        if plan.needs_tool:

            required = (
                required_tool_arguments.get(
                    plan.tool_name,
                    [],
                )
            )

            missing = []

            for argument in required:

                value = (
                    plan.tool_arguments.get(
                        argument
                    )
                )

                if value is None:
                    missing.append(argument)
                    continue

                if (
                    isinstance(value, str)
                    and not value.strip()
                ):
                    missing.append(argument)

            if missing:

                plan.needs_clarification = True

                if (
                    plan.tool_name
                    == "rewrite_reply"
                ):

                    plan.clarification_message = (
                        "I need a draft ID to rewrite. "
                        "Please specify the draft."
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

                # Do not execute incomplete tool calls.
                plan.needs_tool = False
                plan.tool_name = None
                plan.tool_arguments = {}

        return plan