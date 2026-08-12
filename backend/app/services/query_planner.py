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
EXPLICIT CONVERSATIONAL CONTEXT
========================================================

Conversation history may contain structured metadata from
previous assistant tool executions.

Example:

{{
    "role": "assistant",
    "message": "Draft generated successfully.",
    "metadata": {{
        "tool": "generate_reply",
        "action": "generate_reply",
        "email_id": 25,
        "draft_id": 40
    }}
}}

The structured metadata is authoritative for resolving
references to objects created or accessed by previous
actions.

The current conversational object may be referred to as:

- it
- this
- this draft
- that draft
- the draft
- the reply
- this reply
- that reply
- this email
- that email
- the email

For these references:

1. Prefer an explicit ID from the CURRENT user message.
2. Otherwise use the MOST RECENT RELEVANT structured
   metadata from conversation history.
3. Never invent an ID.
4. If the required ID cannot be resolved, request
   clarification.

========================================================
DRAFT CONTEXT
========================================================

A draft context consists primarily of:

- draft_id
- email_id
- tool/action

When the user says:

"make it shorter"
"make the draft shorter"
"make this reply professional"
"approve it"
"reject it"
"save it"
"send it"

and the most recent relevant context contains:

{{
    "draft_id": 40,
    "email_id": 25
}}

use:

"draft_id": 40

Do NOT use the email_id as the draft_id.

Example:

Previous assistant result:

{{
    "tool": "generate_reply",
    "draft_id": 40,
    "email_id": 25
}}

User:

"Make it shorter"

Correct plan:

{{
    "needs_tool": true,
    "tool_name": "rewrite_reply",
    "tool_arguments": {{
        "draft_id": 40,
        "instruction": "make it shorter"
    }}
}}

========================================================
EMAIL CONTEXT
========================================================

When the user refers to:

"this email"
"that email"
"the email"
"it"

in a request requiring an email_id, use the most recent
relevant email_id from structured conversation metadata.

Example:

Previous assistant result:

{{
    "tool": "get_email",
    "email_id": 25
}}

User:

"Generate a reply to it"

Correct plan:

{{
    "needs_tool": true,
    "tool_name": "generate_reply",
    "tool_arguments": {{
        "email_id": 25,
        "tone": "professional"
    }}
}}

========================================================
CONTEXT PRIORITY
========================================================

When resolving IDs, use this priority:

1. Explicit ID in current user message
2. Most recent relevant structured tool result
3. Older structured metadata
4. Clarification

Never invent IDs.

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

- draft_id
- content

========================================================
APPROVE
========================================================

"Approve draft 15"

{{
    "needs_tool": true,
    "tool_name": "approve_draft",
    "tool_arguments": {{
        "draft_id": 15
    }}
}}

"Approve it"

Use the most recent relevant draft_id.

========================================================
REJECT
========================================================

"Reject draft 15"

{{
    "needs_tool": true,
    "tool_name": "reject_draft",
    "tool_arguments": {{
        "draft_id": 15
    }}
}}

"Reject it"

Use the most recent relevant draft_id.

========================================================
SAVE
========================================================

"Save draft 15"

{{
    "needs_tool": true,
    "tool_name": "save_draft",
    "tool_arguments": {{
        "draft_id": 15
    }}
}}

"Save it"

Use the most recent relevant draft_id.

========================================================
UPDATE
========================================================

"Update draft 15"

{{
    "needs_tool": true,
    "tool_name": "update_draft",
    "tool_arguments": {{
        "draft_id": 15
    }}
}}

========================================================
SEND
========================================================

"Send draft 15"

{{
    "needs_tool": true,
    "tool_name": "send_reply",
    "tool_arguments": {{
        "draft_id": 15
    }}
}}

"Send it"

Use the most recent relevant draft_id.

========================================================
ID RULE
========================================================

Current user message has highest priority.

For example:

Previous context:
draft_id = 40

User:
"Send draft 55"

Use:

draft_id = 55

Never let old context override an explicit current ID.

If no ID can be resolved for an action that requires one:

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

    # ======================================================
    # STRUCTURED CONTEXT EXTRACTION
    # ======================================================

    @staticmethod
    def _get_context_ids(
        conversation: list[dict[str, Any]],
    ) -> dict[str, Any]:

        """
        Extract the most recent relevant draft/email context.

        Important:
        We scan newest → oldest.

        A single recent assistant tool result is preferred
        over combining unrelated IDs from different messages.

        Example:

            generate_reply
                email_id=25
                draft_id=40

        becomes:

            {
                "tool": "generate_reply",
                "draft_id": 40,
                "email_id": 25
            }
        """

        context: dict[str, Any] = {}

        # --------------------------------------------------
        # First pass:
        # Find the newest structured tool/action metadata.
        # --------------------------------------------------

        for message in reversed(conversation):

            metadata = message.get("metadata")

            if not isinstance(metadata, dict):
                continue

            tool = metadata.get(
                "tool"
            ) or metadata.get(
                "action"
            )

            draft_id = metadata.get(
                "draft_id"
            )

            email_id = metadata.get(
                "email_id"
            )

            if (
                tool is not None
                or draft_id is not None
                or email_id is not None
            ):

                context["tool"] = tool

                if draft_id is not None:
                    context["draft_id"] = draft_id

                if email_id is not None:
                    context["email_id"] = email_id

                # This is the most recent relevant context.
                break

        # --------------------------------------------------
        # Second pass:
        # Fill missing fields from older metadata only.
        #
        # This avoids mixing newer IDs over an already
        # identified current object.
        # --------------------------------------------------

        if (
            "draft_id" not in context
            or "email_id" not in context
        ):

            for message in reversed(conversation):

                metadata = message.get("metadata")

                if not isinstance(metadata, dict):
                    continue

                if (
                    "draft_id" not in context
                    and metadata.get("draft_id") is not None
                ):
                    context["draft_id"] = (
                        metadata["draft_id"]
                    )

                if (
                    "email_id" not in context
                    and metadata.get("email_id") is not None
                ):
                    context["email_id"] = (
                        metadata["email_id"]
                    )

                if (
                    "draft_id" in context
                    and "email_id" in context
                ):
                    break

        return context

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

        logger.debug(
            "Planner context: %s",
            context,
        )

        logger.debug(
            "Explicit IDs: %s",
            explicit_ids,
        )

        # ==================================================
        # 2. BUILD HISTORY
        # ==================================================

        history_str = (
            "No previous conversation history."
        )

        if conversation:

            history_parts: list[str] = []

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

        # ==================================================
        # 3. CALL LLM
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
                    "Fallback retrieval plan generated "
                    "after planner failure."
                ),
            )

        # ==================================================
        # 4. BASIC NORMALIZATION
        # ==================================================

        plan.reasoning = (
            plan.reasoning or ""
        )

        plan.tool_arguments = (
            plan.tool_arguments or {}
        )

        # ==================================================
        # 5. SEMANTIC NORMALIZATION
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

        # ==================================================
        # 6. VALIDATE / NORMALIZE TOOL
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
        # 7. RESOLVE IDs
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
        # 8. NORMALIZE IDS
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

                        plan.tool_arguments[key] = (
                            normalized_id
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

            else:

                plan.tool_arguments.pop(
                    key,
                    None,
                )

        # ==================================================
        # 9. NORMALIZE TONE
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
        # 10. NORMALIZE REWRITE INSTRUCTION
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
        # 11. REQUIRED ARGUMENTS
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
        # 12. VALIDATE REQUIRED ARGUMENTS
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

                if value is None:

                    missing.append(argument)

                    continue

                if (
                    isinstance(value, str)
                    and not value.strip()
                ):

                    missing.append(argument)

            # ==================================================
            # 13. CLARIFICATION
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
        # 14. FINAL LOGGING
        # ==================================================

        logger.debug(
            "Final normalized QueryPlan: %s",
            plan.model_dump(),
        )

        return plan