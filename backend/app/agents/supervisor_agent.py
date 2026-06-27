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


class SupervisorAgent(BaseAgent):

    name = "supervisor_agent"

    async def execute(
        self,
        state,
    ):

        prompt = ChatPromptTemplate.from_template(
            """
You are the supervisor agent of an AI Email Copilot.

Your job is to decide the next agent.

Available agents:

1. classification
   - classify email
   - extract intelligence
   - summarize

2. reply
   - generate reply draft

Rules:

Choose "reply" when:
- email explicitly asks for response
- sender expects action
- sender asks questions
- reply is required

Choose "classification" for everything else.

EMAIL

Subject:
{subject}

Body:
{body}

Return JSON only:

{{
    "next_agent": "classification"
}}

or

{{
    "next_agent": "reply"
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
                "subject":
                state["subject"],

                "body":
                state["body"][:3000],
            }
        )

        next_agent = result.get(
            "next_agent",
            "classification",
        )

        if next_agent not in [
            "classification",
            "reply",
        ]:
            next_agent = (
                "classification"
            )

        state["next_agent"] = (
            next_agent
        )

        return state