from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from backend.app.agents.base_agent import BaseAgent
from backend.app.core.config import EmailCategory
from backend.app.core.llm import get_llm
from backend.app.services.llm_service import llm_service


class AnalysisAgent(BaseAgent):
    """
    Performs a single-pass analysis of an email.

    Returns:
    - Category
    - Priority
    - Summary
    - Reply Required
    - Extracted Entities
    """

    name = "analysis_agent"

    async def execute(self, state):
        thread_context = state.get("thread_context", "")
        
        # Dynamically inject categories from the core config enum
        categories_str = "\n".join([f"- {c.value}" for c in EmailCategory])

        prompt = ChatPromptTemplate.from_template(
            f"""
You are an AI Email Intelligence engine.

Analyze the email together with any available thread context.

Return a concise intelligence summary.

Determine:
- Category
- Priority
- One concise summary
- Whether the email requires a reply
- Important extracted entities

Categories:
{categories_str}

Priorities:
- urgent
- high
- medium
- low

EMAIL

Subject:
{{subject}}

Sender:
{{sender}}

Body:
{{body}}

Thread Context:
{{thread_context}}

Return ONLY valid JSON.

{{{{
    "category": "",
    "priority": "",
    "summary": "",
    "requires_reply": false,
    "extracted_entities": {{{{
        "organizations": [],
        "people": [],
        "dates": [],
        "action_items": []
    }}}}
}}}}
"""
        )

        llm = get_llm()
        chain = prompt | llm | JsonOutputParser()

        result = await llm_service.ainvoke(
            chain=chain,
            inputs={
                "subject": state["subject"],
                "sender": state["sender"],
                "body": state["body"][:3000],
                "thread_context": thread_context,
            },
        )

        state["category"] = result.get("category")
        state["priority"] = result.get("priority")
        state["summary"] = result.get("summary")
        state["requires_reply"] = result.get("requires_reply", False)
        state["extracted_entities"] = result.get("extracted_entities", {})

        return state