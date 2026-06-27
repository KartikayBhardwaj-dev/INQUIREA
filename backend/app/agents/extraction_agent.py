from langchain_core.prompts import (
    ChatPromptTemplate,
)
from langchain_core.output_parsers import (
    JsonOutputParser,
)

from backend.app.agents.base_agent import (
    BaseAgent,
)

from backend.app.core.llm import llm


class ExtractionAgent(BaseAgent):

    name = "extraction_agent"

    async def execute(
        self,
        state,
    ):

        prompt = ChatPromptTemplate.from_template(
            """
Extract information from this email.

EMAIL

Subject:
{subject}

Body:
{body}

Return JSON only.

{{
    "dates": [],
    "deadlines": [],
    "amounts": [],
    "links": [],
    "organizations": [],
    "contacts": [],
    "action_items": [],
    "requires_reply": false,
    "key_facts": []
}}
"""
        )

        chain = (
            prompt
            | llm
            | JsonOutputParser()
        )

        result = await chain.ainvoke(
    {
        "subject": state["subject"],
        "body": state["body"][:3000],
    }
)

        state["extracted_data"] = result

        return state