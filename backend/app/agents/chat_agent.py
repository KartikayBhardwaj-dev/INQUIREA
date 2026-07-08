from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.app.core.llm import get_llm
from backend.app.services.chat_prompt_builder import ChatPromptBuilder
from backend.app.services.chat_retriever import ChatRetriever
from backend.app.services.query_planner import QueryPlanner

logger = logging.getLogger(__name__)


class ChatAgent:
    """
    AI Inbox Chat Agent.

    Responsibilities
    ----------------
    - Understand the user's question
    - Build a retrieval plan
    - Retrieve relevant emails
    - Build the production RAG prompt
    - Invoke the LLM
    - Return a structured response

    This class orchestrates the complete Level 1
    AI Inbox Chat pipeline.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.retriever = ChatRetriever(db)
        self.planner = QueryPlanner()

    async def chat(
        self,
        question: str,
        conversation: list[dict] | None = None,
    ) -> dict:
        """
        Execute the complete AI Inbox Chat pipeline.

        Pipeline
        --------
        Question
            ↓
        Query Planner
            ↓
        Retriever
            ↓
        Prompt Builder
            ↓
        LLM
            ↓
        Structured Response
        """

        conversation = conversation or []

        logger.info(
            "Processing chat question: %s",
            question,
        )

        # ---------------------------------------------------------
        # Step 1 — Query Planning
        # ---------------------------------------------------------

        try:

            plan = await self.planner.plan(
                question=question,
            )

        except Exception:

            logger.exception(
                "Query planner failed.",
            )
            raise

        logger.info(
            "Query plan generated: %s",
            plan.model_dump(),
        )

        # ---------------------------------------------------------
        # Step 2 — Determine Search Query
        # ---------------------------------------------------------

        search_query = (
            plan.semantic_query
            or question
        )

        logger.debug(
            "Semantic query: %s",
            search_query,
        )

        # ---------------------------------------------------------
        # Step 3 — Retrieve Emails
        # ---------------------------------------------------------

        try:

            emails = self.retriever.retrieve(
                query=search_query,
                limit=plan.retrieve_limit,
                category=plan.category,
                priority=plan.priority,
                sender=plan.sender,
                requires_reply=plan.requires_reply,
                sort_by=plan.sort_by,
                date_from=plan.date_from,
                date_to=plan.date_to,
            )

        except Exception:

            logger.exception(
                "Email retrieval failed.",
            )
            raise

        logger.info(
            "Retrieved %d email(s).",
            len(emails),
        )

        logger.debug(
            "Retrieved IDs: %s",
            [email.id for email in emails],
        )

        # ---------------------------------------------------------
        # Step 4 — Load Email Intelligence
        # ---------------------------------------------------------

        email_data = self.retriever.load_email_data(
            emails,
        )

        logger.debug(
            "Loaded intelligence for %d email(s).",
            len(email_data),
        )

        # ---------------------------------------------------------
        # Build Retrieved Email Metadata
        # ---------------------------------------------------------

        retrieved_emails: list[dict] = []

        for email, intelligence in email_data:

            retrieved_emails.append(
                {
                    "email_id": email.id,
                    "subject": email.subject,
                    "sender": email.sender,
                    "category": (
                        intelligence.category
                        if intelligence
                        else None
                    ),
                    "priority": (
                        intelligence.priority
                        if intelligence
                        else None
                    ),
                    "received_at": email.received_at,
                }
            )

                # ---------------------------------------------------------
        # Step 5 — Handle Empty Retrieval
        # ---------------------------------------------------------

        if not emails:

            logger.info(
                "No matching emails found.",
            )

            return {
                "answer": (
                    "I couldn't find that information "
                    "in your inbox."
                ),
                "sources": [],
                "emails_found": 0,
                "retrieved_emails": [],
                "query_plan": plan.model_dump(),
            }

        # ---------------------------------------------------------
        # Step 6 — Build Production RAG Prompt
        # ---------------------------------------------------------

        prompt = ChatPromptBuilder.build_prompt(
            question=question,
            conversation=conversation,
            email_data=email_data,
        )

        logger.debug(
            "Prompt successfully built.",
        )

        # ---------------------------------------------------------
        # Step 7 — Invoke LLM
        # ---------------------------------------------------------

        llm = get_llm()

        try:

            response = await llm.ainvoke(
                prompt,
            )

            answer = (
                response.content
                if hasattr(response, "content")
                else str(response)
            )

        except Exception:

            logger.exception(
                "LLM invocation failed.",
            )

            return {
                "answer": (
                    "Sorry, I couldn't process your "
                    "request right now."
                ),
                "sources": [
                    email.id
                    for email in emails
                ],
                "emails_found": len(emails),
                "retrieved_emails": retrieved_emails,
                "query_plan": plan.model_dump(),
            }

        logger.info(
            "LLM response generated successfully.",
        )

        # ---------------------------------------------------------
        # Step 8 — Return Structured Response
        # ---------------------------------------------------------

        return {
            "answer": answer,
            "sources": [
                email.id
                for email in emails
            ],
            "emails_found": len(emails),
            "retrieved_emails": retrieved_emails,
            "query_plan": plan.model_dump(),
        }

