from __future__ import annotations

import logging
from typing import Any, Literal
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from backend.app.core.llm import get_llm
from backend.app.core.config import EmailCategory

logger = logging.getLogger(__name__)


class QueryPlan(BaseModel):
    intent: Literal[
        "semantic_search",
        "summarize",
        "sender_lookup",
        "deadline_search",
        "metadata_search",
    ] = Field(description="Overall intent of the user's request.")

    semantic_query: str | None = Field(
        default=None,
        description="Optimized semantic search query. Rewrite vague user questions into better search phrases.",
    )

    category: str | None = Field(default=None, description="Email category filter.")
    priority: Literal["low", "medium", "high", "urgent"] | None = Field(default=None, description="Priority filter.")
    sender: str | None = Field(default=None, description="Specific sender if requested.")
    requires_reply: bool | None = Field(
        default=None,
        description="Whether only emails requiring a reply should be returned.",
    )
    retrieve_limit: int = Field(default=5, ge=1, le=50, description="Maximum number of emails to retrieve.")
    sort_by: Literal["relevance", "date", "priority"] = Field(default="relevance", description="Sorting strategy.")
    date_from: str | None = Field(default=None, description="Inclusive ISO date lower bound.")
    date_to: str | None = Field(default=None, description="Inclusive ISO date upper bound.")
    reasoning: str = Field(description="Short explanation of the chosen retrieval plan.")
    
    needs_tool: bool = Field(
        default=False,
        description="Whether this request should execute a Level 2 tool."
    )
    tool_name: str | None = Field(
        default=None,
        description="Registered tool name to execute."
    )
    tool_arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments passed to the selected tool.",
    )


class QueryPlanner:
    def __init__(self):
        self.parser = PydanticOutputParser(pydantic_object=QueryPlan)
        categories_list = ", ".join([c.value for c in EmailCategory])

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"""
You are the Retrieval Planning Engine for INQUIREA.
Your ONLY responsibility is to transform a user's inbox question into a structured QueryPlan based on their prompt and past conversation history.

You NEVER answer the user's question, summarize emails, or invent facts.
Return ONLY valid JSON matching the provided schema.

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
CONVERSATIONAL CONTEXT RULES
========================================================
Use the provided conversation history to resolve coreferences (e.g., "only those", "from the same sender", "the latest ones").
If the current phrase is dependent on historical context, populate the fields based on what was discussed.

========================================================
SEMANTIC QUERY REWRITING & DATE RULES
========================================================
Rewrite vague expressions into solid search targets. 
CRITICAL DATE RULE: If a date phrase appears inside a contextual search target (e.g., "July 31 Interview", "Assignment due Friday"), do NOT use metadata date fields. Keep the date term inside the `semantic_query`! Only map to metadata dates (`date_from`/`date_to`) if the user explicitly uses tracking boundaries like "received after", "sent yesterday", "this week".

========================================================
CATEGORY DETECTION
========================================================
Populate category ONLY if it explicitly matches one of these valid system terms:
{categories_list}

If it matches any other category concept or you are uncertain, keep it null.

========================================================
PRIORITY & REPLY DETECTION
========================================================
Map priority precisely or default to null. Map `requires_reply` to true if the prompt explicitly looks for actionable or unresolved interactions.

========================================================
LEVEL 2 TOOL ROUTING
========================================================
If the user's request is asking to PERFORM an action rather than retrieve information, set:
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

Examples:
- "Generate a reply for email 25" -> tool_name = "generate_reply", tool_arguments = {{"email_id": 25, "tone": "professional"}}
- "Rewrite this politely" -> tool_name = "rewrite_reply", tool_arguments = {{"tone": "friendly"}}
- "Save draft 12" -> tool_name = "save_draft", tool_arguments = {{"draft_id": 12}}
- "Update draft 12" -> tool_name = "update_draft", tool_arguments = {{"draft_id": 12}}
- "Send draft 12" -> tool_name = "send_reply", tool_arguments = {{"draft_id": 12}}

Default tone for replies is "professional".

========================================================
RETRIEVE LIMIT & SORTING RULES
========================================================
Default: sort_by = relevance. If the user requests latest/recent -> sort_by = date. If highest priority -> sort_by = priority.
Limits: normal/metadata = 5, sender/deadline = 10, summarize = 20.

{{format_instructions}}
""",
                ),
                ("user", "Conversation History:\n{conversation_history}\n\nCurrent Question: {question}"),
            ]
        )

    async def plan(self, question: str, conversation: list[dict] | None = None) -> QueryPlan:
        history_str = "No previous conversation history."
        if conversation:
            history_str = "\n".join(
                [f"{m.get('role', 'user').capitalize()}: {m.get('message', m.get('content', ''))}" for m in conversation]
            )

        llm_instance = get_llm()
        chain = self.prompt.partial(format_instructions=self.parser.get_format_instructions()) | llm_instance | self.parser

        try:
            plan: QueryPlan = await chain.ainvoke(
                {
                    "question": question,
                    "conversation_history": history_str,
                }
            )
        except Exception:
            logger.exception("Failed to parse QueryPlan from LLM response.")
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
                reasoning="Fallback retrieval plan generated after planner failure.",
            )

        # --------------------------------------------------
        # Post-Processing Normalization
        # --------------------------------------------------
        if not plan.semantic_query:
            plan.semantic_query = question
        else:
            plan.semantic_query = plan.semantic_query.strip()

        if plan.priority:
            plan.priority = plan.priority.lower().strip()
            if plan.priority not in {"low", "medium", "high", "urgent"}:
                plan.priority = None

        if plan.category:
            plan.category = plan.category.strip().lower()
            if plan.category not in [c.value for c in EmailCategory]:
                plan.category = None

        if plan.sender:
            plan.sender = plan.sender.strip()
        if plan.date_from:
            plan.date_from = plan.date_from.strip()
        if plan.date_to:
            plan.date_to = plan.date_to.strip()

        plan.retrieve_limit = max(1, min(plan.retrieve_limit, 50))

        if plan.sort_by not in {"relevance", "date", "priority"}:
            plan.sort_by = "relevance"

        if plan.intent == "summarize" and plan.retrieve_limit < 20:
            plan.retrieve_limit = 20

        if plan.intent == "deadline_search" and plan.sort_by != "date":
            plan.sort_by = "date"

        # Validate Tool Execution Parameters
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
            plan.tool_name = plan.tool_name.strip().lower()

        if not plan.needs_tool or plan.tool_name not in valid_tools:
            plan.needs_tool = False
            plan.tool_name = None
            plan.tool_arguments = {}
        else:
            # Ensure proper default parameters for tools
            if plan.tool_name in {"generate_reply", "rewrite_reply"}:
                plan.tool_arguments.setdefault("tone", "professional")
            
            # Cast numeric IDs stringified by LLMs back to integer types
            for key in ("email_id", "draft_id"):
                if key in plan.tool_arguments and isinstance(plan.tool_arguments[key], str):
                    if plan.tool_arguments[key].isdigit():
                        plan.tool_arguments[key] = int(plan.tool_arguments[key])

        return plan