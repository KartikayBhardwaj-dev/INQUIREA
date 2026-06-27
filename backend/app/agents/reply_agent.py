from langchain_core.prompts import (
    ChatPromptTemplate,
)

from backend.app.agents.base_agent import (
    BaseAgent,
)

from backend.app.core.llm import llm


class ReplyAgent(BaseAgent):

    name = "reply_agent"

    async def execute(
        self,
        state,
    ):

        tone = state.get(
            "tone",
            "professional",
        )

        prompt = ChatPromptTemplate.from_template(
            """
You are an email assistant.

Write a reply.

Tone:
{tone}

Possible tones:

- professional
- friendly
- concise
- formal

EMAIL

Subject:
{subject}

Body:
{body}

Summary:
{summary}

Return only draft reply.
"""
        )

        chain = prompt | llm

        result = await chain.ainvoke(
            {
                "tone": tone,
                "subject":
                state["subject"],

                "body":
                state["body"][:3000],

                "summary":
                state.get(
                    "summary",
                    "",
                ),
            }
        )

        state["draft_reply"] = (
            result.content
        )

        return state