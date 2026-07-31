from __future__ import annotations
from pydantic import ConfigDict
import logging
from typing import Any, Literal
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from backend.app.core.llm import get_llm
from backend.app.core.config import EmailCategory

logger = logging.getLogger(__name__)


class QueryPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
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
    reasoning: str = Field(
    default="",
    description="Short explanation..."
)
    
    needs_tool: bool = Field(
        default=False,
        description="Whether this request should execute a Level 2 tool."
    )
    tool_name: str | None = Field(
        default=None,
        description="Registered tool name to execute."
    )
    tool_arguments: dict[str, Any] | None = Field(
    default_factory=dict
)
    needs_clarification: bool = False
    clarification_message: str | None = None


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

IMPORTANT ID RULES

• NEVER invent an email_id.
• NEVER invent a draft_id.
• Priority 1:
Use IDs mentioned in the CURRENT USER QUESTION.

Priority 2:
If the current question does not contain an ID,
look in the conversation history.

Only if neither contains an ID,
return tool_arguments = {{{{}}}} and
needs_clarification = true.
• If no valid ID can be determined, return tool_arguments as  an empty JSON object
• Never copy IDs from these instructions.

Examples

User:
Generate a reply for email <email_id>

Output:
tool_name = "generate_reply"
tool_arguments = {{{{
    "email_id": <email_id>,
    "tone": "professional"
}}}}

User:
Rewrite this politely

Output:
tool_name = "rewrite_reply"
tool_arguments = {{{{
    "tone": "friendly"
}}}}

User:
Save draft <draft_id>

Output:
tool_name = "save_draft"
tool_arguments = {{{{
    "draft_id": <draft_id>
}}}}

User:
Update draft <draft_id>

Output:
tool_name = "update_draft"
tool_arguments = {{{{
    "draft_id": <draft_id>
}}}}

User:
Send draft <draft_id>

Output:
tool_name = "send_reply"
tool_arguments = {{{{
    "draft_id": <draft_id>
}}}}

User:
Approve draft 15

Output:
tool_name = "approve_draft"
tool_arguments = {{{{
    "draft_id": 15
}}}}

User:
Approve draft_reply_id 15

Output:
tool_name = "approve_draft"
tool_arguments = {{{{
    "draft_id": 15
}}}}

User:
Reject draft 15

Output:
tool_name = "reject_draft"
tool_arguments = {{{{
    "draft_id": 15
}}}}
If the conversation contains the draft ID, reuse it.


tool_arguments = {{{{}}}}

Default tone is "professional".


========================================================
RETRIEVE LIMIT & SORTING RULES
========================================================
Default: sort_by = relevance. If the user requests latest/recent -> sort_by = date. If highest priority -> sort_by = priority.
Limits: normal/metadata = 5, sender/deadline = 10, summarize = 20.

{{format_instructions}}

IMPORTANT

Do NOT create nested objects.

Do NOT output keys not defined in the schema.

Every field must exist at the top level.

If tool_arguments is unused, return an empty JSON object.

reasoning must always be present.

Return ONLY the JSON object.
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
            plan.reasoning = plan.reasoning or ""

            plan.tool_arguments = plan.tool_arguments or {}
        except Exception as e:
            logger.exception("Failed to parse QueryPlan from LLM response.")

            logger.exception(e)
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

        required_tool_arguments = {
    "send_reply": ["draft_id"],
    "update_draft": ["draft_id"],
    "approve_draft": ["draft_id"],
    "reject_draft": ["draft_id"],
    "get_email": ["email_id"],
    "generate_reply": ["email_id"],
}
        if plan.tool_name not in valid_tools:
            plan.needs_tool = False
            plan.tool_name = None
            plan.tool_arguments = {}


        if plan.needs_tool:
            required = required_tool_arguments.get(plan.tool_name, [])

            if any(plan.tool_arguments.get(arg) is None for arg in required):
                plan.needs_tool = False
                plan.tool_name = None
                plan.tool_arguments = {}

# always normalize afterwards
        if plan.tool_name in {"generate_reply", "rewrite_reply"}:
            plan.tool_arguments.setdefault("tone", "professional")

        import re

        for key in ("email_id", "draft_id"):
            value = plan.tool_arguments.get(key)

            if isinstance(value, str):
                match = re.search(r"\d+", value)

                if match:
                    plan.tool_arguments[key] = int(match.group())
        
        return plan