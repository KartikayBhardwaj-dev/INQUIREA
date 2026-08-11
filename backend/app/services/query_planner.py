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
    ] = Field(
        description="Overall intent of the user's request."
    )

    semantic_query: str | None = Field(
        default=None,
        description=(
            "Optimized semantic search query. "
            "Rewrite vague user questions into better search phrases."
        ),
    )

    category: str | None = Field(
        default=None,
        description="Email category filter.",
    )

    priority: Literal[
        "low",
        "medium",
        "high",
        "urgent",
    ] | None = Field(
        default=None,
        description="Priority filter.",
    )

    sender: str | None = Field(
        default=None,
        description="Specific sender if requested.",
    )

    requires_reply: bool | None = Field(
        default=None,
        description=(
            "Whether only emails requiring a reply "
            "should be returned."
        ),
    )

    retrieve_limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of emails to retrieve.",
    )

    sort_by: Literal[
        "relevance",
        "date",
        "priority",
    ] = Field(
        default="relevance",
        description="Sorting strategy.",
    )

    date_from: str | None = Field(
        default=None,
        description="Inclusive ISO date lower bound.",
    )

    date_to: str | None = Field(
        default=None,
        description="Inclusive ISO date upper bound.",
    )

    reasoning: str = Field(
        default="",
        description="Short explanation of the planning decision.",
    )

    needs_tool: bool = Field(
        default=False,
        description="Whether this request should execute a Level 2 tool.",
    )

    tool_name: str | None = Field(
        default=None,
        description="Registered tool name to execute.",
    )

    tool_arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments passed to the selected tool.",
    )

    needs_clarification: bool = Field(
        default=False,
        description="Whether the request needs clarification.",
    )

    clarification_message: str | None = Field(
        default=None,
        description="Message explaining what information is missing.",
    )


class QueryPlanner:

    def __init__(self):
        self.parser = PydanticOutputParser(
            pydantic_object=QueryPlan
        )

        categories_list = ", ".join(
            [c.value for c in EmailCategory]
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"""
You are the Retrieval Planning Engine for INQUIREA.

Your ONLY responsibility is to transform the user's request
into a structured QueryPlan.

You NEVER answer the user's question.
You NEVER summarize emails.
You NEVER invent IDs.
You ONLY return valid JSON matching the QueryPlan schema.

========================================================
AVAILABLE INTENTS
========================================================

1. semantic_search
2. summarize
3. metadata_search
4. sender_lookup
5. deadline_search

Choose exactly ONE intent.

========================================================
CONVERSATIONAL CONTEXT
========================================================

Use conversation history to resolve references such as:

- "it"
- "this draft"
- "that email"
- "make it shorter"
- "make it professional"
- "make it friendlier"
- "change the ending"
- "regenerate it"
- "approve it"
- "send it"

If the current request depends on a previous draft,
find the draft_id from conversation history.

If the current request contains an explicit ID,
ALWAYS prefer the current request's ID.

NEVER invent an ID.

========================================================
LEVEL 2 TOOL ROUTING
========================================================

If the user wants an ACTION rather than information,
set:

needs_tool = true

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

========================================================
GENERATE REPLY
========================================================

Example:

User:
Generate a reply to email 10.

Output:

needs_tool = true
tool_name = "generate_reply"

tool_arguments = {{
    "email_id": 10,
    "tone": "professional"
}}

========================================================
REWRITE REPLY
========================================================

IMPORTANT:

rewrite_reply MUST use:

draft_id

and an instruction.

The instruction is NOT limited to tone.

Use:

"instruction"

for requests such as:

- make it shorter
- make it concise
- make it more professional
- make it friendly
- make it friendlier
- change the ending
- remove unnecessary details
- make it clearer
- simplify this
- make it more formal
- make it less formal

Examples:

User:
Make draft 15 shorter.

Output:

needs_tool = true
tool_name = "rewrite_reply"

tool_arguments = {{
    "draft_id": 15,
    "instruction": "make it shorter"
}}

User:
Make draft 15 more professional.

Output:

needs_tool = true
tool_name = "rewrite_reply"

tool_arguments = {{
    "draft_id": 15,
    "instruction": "make it more professional"
}}

User:
Change the ending.

If conversation history identifies draft 15:

needs_tool = true
tool_name = "rewrite_reply"

tool_arguments = {{
    "draft_id": 15,
    "instruction": "change the ending"
}}

User:
Make it friendlier.

If conversation history identifies draft 15:

needs_tool = true
tool_name = "rewrite_reply"

tool_arguments = {{
    "draft_id": 15,
    "instruction": "make it friendlier"
}}

========================================================
REWRITE INSTRUCTION RULE
========================================================

For rewrite_reply:

- Always include draft_id.
- Always include instruction.
- Preserve the user's intended instruction.
- Do NOT convert every instruction into a tone.
- "shorter" is an instruction.
- "more professional" is an instruction.
- "change the ending" is an instruction.
- "remove unnecessary details" is an instruction.

The instruction should be a concise normalized version
of the user's request.

========================================================
EDIT DRAFT
========================================================

Use edit_draft only when the user explicitly provides
the replacement draft content.

Example:

User:
Replace the draft with:
Hi Google Team,

Thanks for reaching out.

Best,
Kartikay

Output:

needs_tool = true
tool_name = "edit_draft"

tool_arguments = {{
    "draft_id": <draft_id>,
    "content": "Hi Google Team,\\n\\nThanks for reaching out.\\n\\nBest,\\nKartikay"
}}

The draft_id may come from conversation history.

========================================================
APPROVE
========================================================

User:
Approve draft 15.

Output:

needs_tool = true
tool_name = "approve_draft"

tool_arguments = {{
    "draft_id": 15
}}

User:
Approve it.

If conversation history identifies draft 15:

tool_name = "approve_draft"

tool_arguments = {{
    "draft_id": 15
}}

========================================================
REJECT
========================================================

User:
Reject draft 15.

Output:

needs_tool = true
tool_name = "reject_draft"

tool_arguments = {{
    "draft_id": 15
}}

========================================================
SAVE DRAFT
========================================================

User:
Save draft 15 to Gmail.

Output:

needs_tool = true
tool_name = "save_draft"

tool_arguments = {{
    "draft_id": 15
}}

========================================================
UPDATE DRAFT
========================================================

User:
Update draft 15.

Output:

needs_tool = true
tool_name = "update_draft"

tool_arguments = {{
    "draft_id": 15
}}

========================================================
SEND REPLY
========================================================

User:
Send draft 15.

Output:

needs_tool = true
tool_name = "send_reply"

tool_arguments = {{
    "draft_id": 15
}}

User:
Send it.

If conversation history identifies draft 15:

tool_name = "send_reply"

tool_arguments = {{
    "draft_id": 15
}}

========================================================
ID RULES
========================================================

NEVER invent email_id.
NEVER invent draft_id.

Priority 1:
Use an ID explicitly mentioned in the CURRENT USER QUESTION.

Priority 2:
Use an ID from conversation history.

If neither exists:

tool_arguments = {{}}
needs_clarification = true

Do NOT execute the tool.

========================================================
TONE
========================================================

Tone is optional metadata.

For generate_reply:
default tone = "professional"

For rewrite_reply:
DO NOT add a tone field unless the instruction itself
is specifically a tone request.

The primary rewrite field is:

"instruction"

Examples:

"Make it shorter"
-> instruction = "make it shorter"

"Make it more professional"
-> instruction = "make it more professional"

"Make it friendly"
-> instruction = "make it friendly"

"Change the ending"
-> instruction = "change the ending"

========================================================
SEMANTIC SEARCH
========================================================

If the request is information retrieval rather than an action,
do not use a tool.

Use the retrieval fields normally.

========================================================
DATE RULES
========================================================

If a date phrase appears inside a contextual search target
such as:

"July 31 interview"
"assignment due Friday"

keep it inside semantic_query.

Only use date_from/date_to when the user explicitly requests
date filtering such as:

- received after
- received before
- sent yesterday
- received this week

========================================================
CATEGORY
========================================================

Populate category ONLY if it explicitly matches one of:

{categories_list}

Otherwise use null.

========================================================
PRIORITY
========================================================

Map:

low
medium
high
urgent

Otherwise use null.

========================================================
RETRIEVAL LIMIT
========================================================

Default:
5

Sender/deadline:
10

Summarize:
20

Maximum:
50

========================================================
SORTING
========================================================

Default:
relevance

latest/recent:
date

highest priority:
priority

========================================================
IMPORTANT OUTPUT RULES
========================================================

Return ONLY valid JSON.

Do NOT create nested objects outside tool_arguments.

Do NOT create fields that are not defined by QueryPlan.

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

    async def plan(
        self,
        question: str,
        conversation: list[dict] | None = None,
    ) -> QueryPlan:

        history_str = "No previous conversation history."

        if conversation:
            history_str = "\n".join(
                [
                    (
                        f"{m.get('role', 'user').capitalize()}: "
                        f"{m.get('message', m.get('content', ''))}"
                    )
                    for m in conversation
                ]
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
                "Failed to parse QueryPlan from LLM response."
            )

            return QueryPlan(
                intent="semantic_search",
                semantic_query=question,
                category=None,
                priority=None,
                sender=None,
                requires_reply=None,
                retrieve_limit=5,
                sort_by="relevance",
                date_from=None,
                date_to=None,
                needs_tool=False,
                tool_name=None,
                tool_arguments={},
                reasoning=(
                    "Fallback retrieval plan generated "
                    "after planner failure."
                ),
            )

        # --------------------------------------------------
        # Normalize basic fields
        # --------------------------------------------------

        plan.reasoning = plan.reasoning or ""
        plan.tool_arguments = plan.tool_arguments or {}

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
                c.value for c in EmailCategory
            ]:
                plan.category = None

        if plan.sender:
            plan.sender = plan.sender.strip()

        if plan.date_from:
            plan.date_from = plan.date_from.strip()

        if plan.date_to:
            plan.date_to = plan.date_to.strip()

        plan.retrieve_limit = max(
            1,
            min(plan.retrieve_limit, 50),
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
        # Normalize tool name
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
        # Normalize IDs
        # --------------------------------------------------

        for key in ("email_id", "draft_id"):
            value = plan.tool_arguments.get(key)

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
        # Required arguments
        # --------------------------------------------------

        required_tool_arguments = {
            "send_reply": ["draft_id"],
            "update_draft": ["draft_id"],
            "save_draft": ["draft_id"],
            "approve_draft": ["draft_id"],
            "reject_draft": ["draft_id"],
            "get_email": ["email_id"],
            "generate_reply": ["email_id"],
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
        # Tool-specific normalization
        # --------------------------------------------------

        if plan.tool_name == "generate_reply":
            plan.tool_arguments.setdefault(
                "tone",
                "professional",
            )

        if plan.tool_name == "rewrite_reply":

            instruction = plan.tool_arguments.get(
                "instruction"
            )

            if instruction is not None:
                instruction = str(
                    instruction
                ).strip()

                if instruction:
                    plan.tool_arguments[
                        "instruction"
                    ] = instruction
                else:
                    plan.tool_arguments.pop(
                        "instruction",
                        None,
                    )

        # --------------------------------------------------
        # Validate required arguments
        # --------------------------------------------------

        if plan.needs_tool:

            required = required_tool_arguments.get(
                plan.tool_name,
                [],
            )

            missing = [
                argument
                for argument in required
                if (
                    plan.tool_arguments.get(argument)
                    is None
                    or (
                        isinstance(
                            plan.tool_arguments.get(argument),
                            str,
                        )
                        and not plan.tool_arguments.get(
                            argument
                        ).strip()
                    )
                )
            ]

            if missing:

                plan.needs_clarification = True

                if plan.tool_name == "rewrite_reply":
                    plan.clarification_message = (
                        "I need the draft you want to "
                        "rewrite and the rewrite instruction."
                    )

                elif plan.tool_name == "edit_draft":
                    plan.clarification_message = (
                        "I need the draft ID and the "
                        "new draft content."
                    )

                else:
                    plan.clarification_message = (
                        f"Missing required information: "
                        f"{', '.join(missing)}."
                    )

                # Do NOT execute incomplete tool calls.
                plan.needs_tool = False
                plan.tool_name = None
                plan.tool_arguments = {}

        return plan