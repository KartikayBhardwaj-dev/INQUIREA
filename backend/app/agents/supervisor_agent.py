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
You are the routing agent for an AI Email Copilot.

Your ONLY job is to decide which downstream agent should process the email.

Email Subject:
{subject}

Email Body:
{body}

Available routes:

1. analysis
- classify the email
- determine priority
- extract structured information
- summarize the email
- summarize the thread

2. reply
- generate a draft reply

Choose "reply" ONLY when the user is expected to send a response.

Examples:
✓ asks a question
✓ requests information
✓ requests an action
✓ requests confirmation
✓ expects a decision
✓ asks for feedback

Choose "analysis" for:
✓ newsletters
✓ notifications
✓ invoices
✓ receipts
✓ shipping updates
✓ automated emails
✓ informational emails
✓ announcements

Return ONLY valid JSON.

{{
    "next_agent": "analysis"
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

        try:
            result = await chain.ainvoke(
        {
            "subject": state["subject"],
            "body": state["body"][:3000],
        }
    )
        except Exception:
            result = {
        "next_agent": "analysis"
    }

        next_agent = (
    result.get("next_agent", "analysis")
    .strip()
    .lower()
)

        if next_agent not in {"analysis", "reply"}:
            next_agent = "analysis"

        state["next_agent"] = next_agent

        return state