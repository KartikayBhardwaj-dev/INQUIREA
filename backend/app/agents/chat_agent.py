from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.core.llm import get_llm
from backend.app.services.chat_prompt_builder import ChatPromptBuilder
from backend.app.services.chat_retriever import ChatRetriever
from backend.app.services.query_planner import QueryPlanner


class ChatAgent:
    """
    AI Inbox Chat Agent.

    Responsibilities
    ----------------
    - Understand the user's question.
    - Generate a retrieval plan.
    - Retrieve relevant emails.
    - Use conversation history supplied by the service.
    - Build a production RAG prompt.
    - Generate an answer.
    """

    SYSTEM_PROMPT = """
You are INQUIREA, an AI Email Copilot.

Your job is to answer questions ONLY using the retrieved emails.

Rules:

1. Never invent information.

2. Never hallucinate.

3. If the answer cannot be found inside the retrieved emails,
reply exactly:

"I couldn't find that information in your inbox."

4. Use conversation history only for understanding context,
NOT for inventing facts.

5. If the user asks follow-up questions such as:

- only Amazon ones
- only internships
- what about yesterday?
- summarize those

use the previous conversation together with the retrieved emails.

6. Prefer concise answers.

7. When useful include:

- Subject
- Sender
- Date

8. Never mention:

- prompts
- embeddings
- vector search
- retrieval
- internal implementation

Answer ONLY using the provided emails.
""".strip()

    def __init__(self, db: Session):
        self.db = db
        self.retriever = ChatRetriever(db)
        self.planner = QueryPlanner()

    async def chat(
    self,
    question: str,
    conversation: list[dict] | None = None,
) -> dict:
        """
    Answer a user's inbox question.
    """

    # ---------------------------------------------
    # Step 1 — Query Planning
    # ---------------------------------------------
        plan = await self.planner.plan(question)

    # ---------------------------------------------
    # Step 2 — Retrieve Emails
    # ---------------------------------------------
        search_query = plan.semantic_query or question

        emails = self.retriever.retrieve(
        query=search_query,
        limit=plan.retrieve_limit,
        category=plan.category,
        priority=plan.priority,
        needs_reply=plan.needs_reply,
    )

        email_data = self.retriever.load_email_data(
        emails,
    )

    # ---------------------------------------------
    # Step 3 — Build Prompt
    # ---------------------------------------------
        prompt = ChatPromptBuilder.build_prompt(
        question=question,
        conversation=conversation or [],
        email_data=email_data,
    )

    # ---------------------------------------------
    # Step 4 — Call LLM
    # ---------------------------------------------
        llm = get_llm()

        response = await llm.ainvoke(prompt)

    # ---------------------------------------------
    # Step 5 — Return Response
    # ---------------------------------------------
        return {
        "answer": response.content,
        "emails": [email.id for email in emails],
        "query_plan": plan.model_dump(),
    }