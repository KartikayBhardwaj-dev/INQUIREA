from langchain_core.prompts import (
    ChatPromptTemplate,
)

from backend.app.agents.base_agent import (
    BaseAgent,
)

from backend.app.core.llm import llm


class SummaryAgent(BaseAgent):

    name = "summary_agent"

    async def execute(
        self,
        state,
    ):

        thread_context = (
            state.get(
                "thread_context",
                "",
            )
        )

        prompt = ChatPromptTemplate.from_template(
            """
Create:

1. Email Summary
2. Thread Summary

EMAIL

Subject:
{subject}

Body:
{body}

THREAD

{thread_context}

Return:

EMAIL SUMMARY:
...

THREAD SUMMARY:
...
"""
        )

        chain = prompt | llm

        result = await chain.ainvoke(
            {
                "subject":
                state["subject"],

                "body":
                state["body"][:3000],

                "thread_context":
                thread_context,
            }
        )

        response = result.content

        email_summary = response
        thread_summary = response

        if "THREAD SUMMARY:" in response:

            parts = response.split(
                "THREAD SUMMARY:"
            )

            email_summary = (
                parts[0]
                .replace(
                    "EMAIL SUMMARY:",
                    "",
                )
                .strip()
            )

            thread_summary = (
                parts[1]
                .strip()
            )

        state["summary"] = (
            email_summary
        )

        state["thread_summary"] = (
            thread_summary
        )

        return state