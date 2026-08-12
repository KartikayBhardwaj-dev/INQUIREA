from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.llm import get_llm
from backend.app.services.chat_prompt_builder import ChatPromptBuilder
from backend.app.services.chat_retriever import ChatRetriever
from backend.app.services.query_planner import (
    QueryPlanner,
    QueryPlan,
)
from backend.app.services.chat_tool_executer import (
    ChatToolExecutor,
)

logger = logging.getLogger(__name__)


class ChatAgent:
    """
    AI Inbox Chat Agent.

    Orchestrates:

        Planner
           ↓
        Tool / RAG
           ↓
        Structured response

    The agent also extracts structured action state so that
    future conversational requests can resolve references such as:

        "it"
        "make it shorter"
        "approve it"
        "send it"
    """

    def __init__(self, db: Session):

        self.db = db

        self.retriever = ChatRetriever(db)

        self.planner = QueryPlanner()

        self.tool_executor = ChatToolExecutor(
            self.db
        )

    async def chat(
        self,
        question: str,
        conversation: list[dict[str, Any]] | None = None,
        user_id: int | None = None,
    ) -> dict[str, Any]:

        conversation = conversation or []

        logger.info(
            "Processing chat question: %s "
            "(User ID: %s)",
            question,
            user_id,
        )

        # --------------------------------------------------
        # Planner
        # --------------------------------------------------

        try:

            plan: QueryPlan = (
                await self.planner.plan(
                    question=question,
                    conversation=conversation,
                )
            )

        except Exception:

            logger.exception(
                "Query planner failed."
            )

            return {
    "answer": (
        "I ran into an issue planning "
        "your request. Please try "
        "rephrasing your question."
    ),
    "tool": None,
    "tool_result": None,
    "query_plan": {},
}

        logger.info(
            "Query plan generated: %s",
            plan.model_dump(),
        )

        # --------------------------------------------------
        # Clarification
        # --------------------------------------------------

        if plan.needs_clarification:

            return {
    "answer": (
        plan.clarification_message
        or "I need some more information "
        "to complete that action."
    ),
    "tool": None,
    "tool_result": None,
    "query_plan": plan.model_dump(),
}

        # --------------------------------------------------
        # Tool execution
        # --------------------------------------------------

        if (
            plan.needs_tool
            and plan.tool_name
        ):

            return await self._handle_tool_request(
                plan,
                user_id=user_id,
            )

        # --------------------------------------------------
        # Normal retrieval
        # --------------------------------------------------

        return await self._handle_retrieval_request(
            question=question,
            conversation=conversation,
            plan=plan,
        )

    async def _handle_tool_request(
    self,
    plan: QueryPlan,
    user_id: int | None = None,
) -> dict[str, Any]:

        logger.info(
        "Planner selected tool '%s'.",
        plan.tool_name,
    )

    # --------------------------------------------------
    # Build tool arguments
    # --------------------------------------------------

        tool_args = {
        **plan.tool_arguments
    }

    # user_id is injected by backend.
    # Planner must never control authentication identity.
        if user_id is not None:
            tool_args["user_id"] = user_id

    # --------------------------------------------------
    # Execute tool
    # --------------------------------------------------

        try:

            tool_result = await self.tool_executor.execute(
            tool_name=plan.tool_name,
            **tool_args,
        )

        except Exception as exc:

            logger.exception(
            "Tool '%s' execution failed.",
            plan.tool_name,
        )

            error_message = str(exc)

            return {
            "answer": error_message,
            "tool": plan.tool_name,
            "tool_result": None,
            "error": self._build_tool_error(
                message=error_message,
                tool_name=plan.tool_name,
            ),
            "query_plan": plan.model_dump(),
        }

    # --------------------------------------------------
    # Tool returned an explicit failure
    # --------------------------------------------------

        if not tool_result.get("success"):

            error_message = tool_result.get(
            "error",
            "An unknown tool error occurred.",
        )

        # Handle either:
        #
        # error = "some message"
        #
        # or:
        #
        # error = {
        #     "code": "...",
        #     "message": "..."
        # }
        #

            if isinstance(error_message, dict):

                error = {
                "code": error_message.get(
                    "code",
                    "TOOL_ERROR",
                ),
                "message": error_message.get(
                    "message",
                    "An unknown tool error occurred.",
                ),
            }

            else:

                error = self._build_tool_error(
                message=str(error_message),
                tool_name=plan.tool_name,
            )

            return {
            "answer": error["message"],
            "tool": plan.tool_name,
            "tool_result": None,
            "error": error,
            "query_plan": plan.model_dump(),
        }

    # --------------------------------------------------
    # Extract actual tool result
    # --------------------------------------------------

        result = tool_result.get(
        "result",
        {},
    )

    # --------------------------------------------------
    # Normalize successful result
    # --------------------------------------------------

        if isinstance(result, dict):

            structured_result = result

            answer = (
            result.get("message")
            or result.get("status")
            or f"Action '{plan.tool_name}' "
               "completed successfully."
        )

        elif isinstance(result, str):

            structured_result = {
            "details": result,
        }

            answer = result

        else:

            structured_result = {
            "details": result,
        }

            answer = (
            f"Action '{plan.tool_name}' "
            "completed successfully."
        )

    # --------------------------------------------------
    # Build conversation/action metadata
    # --------------------------------------------------

        context_metadata: dict[str, Any] = {
        "tool": plan.tool_name,
        "action": plan.tool_name,
    }

    # --------------------------------------------------
    # Preserve email_id
    # --------------------------------------------------

        email_id = None

        if isinstance(structured_result, dict):

            email_id = structured_result.get(
            "email_id"
        )

        if email_id is None:

            email_id = plan.tool_arguments.get(
            "email_id"
        )

        if email_id is not None:

            context_metadata["email_id"] = email_id

    # --------------------------------------------------
    # Preserve draft_id
    # --------------------------------------------------

        draft_id = None

        if isinstance(structured_result, dict):

            draft_id = structured_result.get(
            "draft_id"
        )

        if draft_id is None:

            draft_id = plan.tool_arguments.get(
            "draft_id"
        )

        if draft_id is not None:

            context_metadata["draft_id"] = draft_id

        logger.debug(
        "Structured tool state: %s",
        context_metadata,
    )

    # --------------------------------------------------
    # Successful response
    # --------------------------------------------------

        return {
        "answer": answer,
        "tool": plan.tool_name,
        "tool_result": structured_result,
        "error": None,
        "query_plan": plan.model_dump(),
        "context_metadata": context_metadata,
    }
    def _build_tool_error(
    self,
    message: str,
    tool_name: str,
) -> dict[str, str]:

        message_lower = message.lower()

    # --------------------------------------------------
    # Approval errors
    # --------------------------------------------------

        if (
        "approval" in message_lower
        or "approved" in message_lower
        or "pending approval" in message_lower
    ):
            return {
            "code": "APPROVAL_REQUIRED",
            "message": message,
        }

    # --------------------------------------------------
    # Ownership / authorization errors
    # --------------------------------------------------

        if (
        "do not own" in message_lower
        or "not authorized" in message_lower
        or "unauthorized" in message_lower
        or "ownership" in message_lower
    ):
            return {
            "code": "FORBIDDEN",
            "message": message,
        }

    # --------------------------------------------------
    # Missing draft
    # --------------------------------------------------

        if (
        "draft" in message_lower
        and (
            "not found" in message_lower
            or "does not exist" in message_lower
        )
    ):
            return {
            "code": "DRAFT_NOT_FOUND",
            "message": message,
        }

    # --------------------------------------------------
    # Missing Gmail draft
    # --------------------------------------------------

        if (
        "gmail draft" in message_lower
            and (
            "no gmail draft" in message_lower
            or "gmail draft id" in message_lower
            or "save draft" in message_lower
        )
    ):
            return {
            "code": "GMAIL_DRAFT_REQUIRED",
            "message": message,
        }

    # --------------------------------------------------
    # Missing required input
    # --------------------------------------------------

        if (
        "required" in message_lower
        or "missing" in message_lower
    ):
            return {
            "code": "INVALID_INPUT",
            "message": message,
        }

    # --------------------------------------------------
    # Gmail errors
    # --------------------------------------------------

        if "gmail" in message_lower:

            return {
            "code": "GMAIL_ERROR",
            "message": message,
        }

    # --------------------------------------------------
    # Fallback
    # --------------------------------------------------

        return {
        "code": "TOOL_ERROR",
        "message": message,
    }
    async def _handle_retrieval_request(
        self,
        question: str,
        conversation: list[dict[str, Any]],
        plan: QueryPlan,
    ) -> dict[str, Any]:

        search_query = (
            plan.semantic_query
            or question
        )

        emails = self._retrieve_emails(
            search_query,
            plan,
        )

        if emails is None:

            return {
                "answer": (
                    "I encountered an error "
                    "looking up your emails. "
                    "Let's try that search again "
                    "in a moment."
                ),
                "sources": [],
                "emails_found": 0,
                "retrieved_emails": [],
                "query_plan": plan.model_dump(),
            }

        email_data, retrieved_emails = (
            self._build_email_context(
                emails
            )
        )

        if not emails:

            return await self._generate_empty_state(
                question,
                plan,
            )

        return await self._generate_rag_response(
            question=question,
            conversation=conversation,
            email_data=email_data,
            emails=emails,
            retrieved_emails=retrieved_emails,
            plan=plan,
        )

    def _retrieve_emails(
        self,
        search_query: str,
        plan: QueryPlan,
    ) -> list[Any] | None:

        try:

            return self.retriever.retrieve(
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
                "Email retrieval failed."
            )

            return None

    def _build_email_context(
        self,
        emails: list[Any],
    ) -> tuple[
        list[tuple[Any, Any]],
        list[dict[str, Any]],
    ]:

        email_data = (
            self.retriever.load_email_data(
                emails
            )
        )

        retrieved_emails: list[
            dict[str, Any]
        ] = []

        for email, intelligence in email_data:

            extracted = (
                intelligence.extracted_data
                if (
                    intelligence
                    and intelligence.extracted_data
                )
                else {}
            )

            entities = extracted.get(
                "extracted_entities",
                extracted.get(
                    "entities",
                    {},
                ),
            )

            retrieved_emails.append(
                {
                    "email_id": email.id,
                    "subject": email.subject,
                    "sender": email.sender,
                    "gmail_message_id": (
                        email.gmail_message_id
                    ),
                    "recipient": email.recipient,
                    "received_at": email.received_at,
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
                    "summary": (
                        intelligence.summary
                        if intelligence
                        else None
                    ),
                    "requires_reply": extracted.get(
                        "requires_reply",
                        False,
                    ),
                    "entities": entities,
                    "action_items": (
                        entities.get(
                            "action_items",
                            [],
                        )
                        if isinstance(
                            entities,
                            dict,
                        )
                        else []
                    ),
                }
            )

        return (
            email_data,
            retrieved_emails,
        )

    async def _generate_empty_state(
        self,
        question: str,
        plan: QueryPlan,
    ) -> dict[str, Any]:

        llm = get_llm()

        fallback_prompt = f"""
You are INQUIREA, an AI Email Copilot.

The user asked a question, but the database search
returned zero matching emails.

USER QUESTION:
"{question}"

FILTERS:
Category: {plan.category}
Priority: {plan.priority}
Sender: {plan.sender}
Requires Reply: {plan.requires_reply}

Output ONLY the direct response to the user.
""".strip()

        try:

            response = await llm.ainvoke(
                fallback_prompt
            )

            answer = (
                response.content
                if hasattr(
                    response,
                    "content",
                )
                else str(response)
            )

        except Exception:

            answer = (
                "I couldn't find that "
                "information in your inbox."
            )

        return {
            "answer": str(answer).strip(),
            "sources": [],
            "emails_found": 0,
            "retrieved_emails": [],
            "query_plan": plan.model_dump(),
        }

    async def _generate_rag_response(
        self,
        question: str,
        conversation: list[dict[str, Any]],
        email_data: list[tuple[Any, Any]],
        emails: list[Any],
        retrieved_emails: list[dict[str, Any]],
        plan: QueryPlan,
    ) -> dict[str, Any]:

        prompt = ChatPromptBuilder.build_prompt(
            question=question,
            conversation=conversation,
            email_data=email_data,
        )

        llm = get_llm()

        try:

            response = await llm.ainvoke(
                prompt
            )

            answer = (
                response.content
                if hasattr(
                    response,
                    "content",
                )
                else str(response)
            )

        except Exception:

            return {
                "answer": (
                    "Sorry, I ran into an error "
                    "while processing your email "
                    "context records."
                ),
                "sources": [
                    email.id
                    for email in emails
                ],
                "emails_found": len(emails),
                "retrieved_emails": (
                    retrieved_emails
                ),
                "query_plan": plan.model_dump(),
            }

        return {
            "answer": str(answer),
            "sources": [
                email.id
                for email in emails
            ],
            "emails_found": len(emails),
            "retrieved_emails": retrieved_emails,
            "query_plan": plan.model_dump(),
        }