from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from backend.app.agents.base_agent import BaseAgent
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

        subject = state.get(
            "subject",
            "",
        )

        body = state.get(
            "body",
            "",
        )

        summary = state.get(
            "summary",
            "",
        )

        existing_draft = state.get(
            "draft_reply",
        )

        instruction = state.get(
            "instruction",
        )

        # =====================================================
        # REWRITE EXISTING DRAFT
        # =====================================================

        if existing_draft and instruction:
            prompt = ChatPromptTemplate.from_template(
                """
You are an email editing assistant.

Your task is to MODIFY the existing draft according to the
user's instruction.

IMPORTANT RULES:

1. Start from the EXISTING DRAFT.
2. Apply the user's instruction exactly.
3. Preserve all parts of the existing draft that the user did
   not ask you to change.
4. Do NOT write a completely new email.
5. Do NOT invent personal information.
6. Do NOT add placeholders such as:
   [Your Name]
   [Your Position]
   [Your Company]
   [Contact Information]
   unless the user explicitly asks for them.
7. If the user provides a specific value, use that exact value.
8. If the user asks to remove something, remove it completely.
9. Keep the same subject unless the user explicitly asks to
   change it.
10. Return ONLY the revised email. Do not explain your changes.

Tone:
{tone}

Original Email Subject:
{subject}

Original Email Body:
{body}

Existing Draft:
{existing_draft}

User's Rewrite Instruction:
{instruction}

Return only the revised draft.
"""
            )

            chain = prompt | llm

            result = await chain.ainvoke(
                {
                    "tone": tone,
                    "subject": subject,
                    "body": body[:3000],
                    "existing_draft": existing_draft,
                    "instruction": instruction.strip(),
                }
            )

            state["draft_reply"] = result.content

            return state

        # =====================================================
        # GENERATE NEW DRAFT
        # =====================================================

        prompt = ChatPromptTemplate.from_template(
            """
You are an email assistant.

Write a reply to the email below.

Tone:
{tone}

Possible tones:

- professional
- friendly
- concise
- formal

IMPORTANT RULES:

1. Write a natural email reply.
2. Do not invent personal information about the sender
   or recipient.
3. Do not invent names, phone numbers, companies, positions,
   dates, prices, commitments, or other facts that are not
   present in the email or provided by the user.
4. Do not use placeholders such as:
   [Your Name]
   [Your Position]
   [Your Company]
   [Contact Information]
5. If a personal signature is not available, end the email
   naturally without inventing one.
6. Return ONLY the draft reply.

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
                "subject": subject,
                "body": body[:3000],
                "summary": summary,
            }
        )

        state["draft_reply"] = result.content

        return state