from __future__ import annotations

import logging
from typing import Any
from sqlalchemy.orm import Session

from backend.app.core.llm import get_llm
from backend.app.services.chat_prompt_builder import ChatPromptBuilder
from backend.app.services.chat_retriever import ChatRetriever
from backend.app.services.query_planner import QueryPlanner, QueryPlan
from backend.app.services.chat_tool_executer import ChatToolExecutor

logger = logging.getLogger(__name__)


class ChatAgent:
    """
    AI Inbox Chat Agent.
    Orchestrates Level 1 (RAG) and Level 2 (Tool Execution) pipelines.
    """

    def __init__(self, db: Session):
        self.db = db
        self.retriever = ChatRetriever(db)
        self.planner = QueryPlanner()
        self.tool_executor = ChatToolExecutor(self.db)

    async def chat(
        self, 
        question: str, 
        conversation: list[dict] | None = None,
        user_id: int | None = None
    ) -> dict[str, Any]:
        conversation = conversation or []
        logger.info("Processing chat question: %s (User ID: %s)", question, user_id)

        try:
            plan: QueryPlan = await self.planner.plan(
                question=question,
                conversation=conversation
            )
        except Exception:
            logger.exception("Query planner failed.")
            return {
                "answer": "I ran into an issue planning your request. Please try rephrasing your question.",
                "sources": [],
                "emails_found": 0,
                "retrieved_emails": [],
                "query_plan": {},
            }

        logger.info("Query plan generated: %s", plan.model_dump())

        if plan.needs_tool and plan.tool_name:
            return await self._handle_tool_request(plan, user_id=user_id)
        
        return await self._handle_retrieval_request(question, conversation, plan)

    async def _handle_tool_request(self, plan: QueryPlan, user_id: int | None = None) -> dict[str, Any]:
        """Handles Level 2 Tool Execution branching."""
        logger.info("Planner selected tool '%s'.", plan.tool_name)

        tool_args = {**plan.tool_arguments}
        if user_id is not None:
            tool_args["user_id"] = user_id

        tool_result = await self.tool_executor.execute(
            tool_name=plan.tool_name, # type: ignore[arg-type]
            **tool_args,
        )

        if tool_result.get("success"):
            result = tool_result.get("result", {})
            
            if isinstance(result, str):
                answer = result
            elif isinstance(result, dict):
                answer = (
                    result.get("message")
                    or result.get("draft")
                    or f"Action '{plan.tool_name}' completed successfully."
                )
            else:
                answer = f"Action '{plan.tool_name}' completed successfully."

            return {
                "answer": answer,
                "tool": plan.tool_name,
                "tool_result": result if isinstance(result, dict) else {"details": result},
                "sources": [],
                "emails_found": result.get("emails_found", 0) if isinstance(result, dict) else 0,
                "retrieved_emails": result.get("retrieved_emails", []) if isinstance(result, dict) else [],
                "query_plan": plan.model_dump(),
            }

        return {
            "answer": tool_result.get("error", "An unknown tool error occurred."),
            "tool": plan.tool_name,
            "sources": [],
            "emails_found": 0,
            "retrieved_emails": [],
            "query_plan": plan.model_dump(),
        }

    async def _handle_retrieval_request(
        self, question: str, conversation: list[dict], plan: QueryPlan
    ) -> dict[str, Any]:
        search_query = plan.semantic_query or question
        emails = self._retrieve_emails(search_query, plan)
        
        if emails is None:
            return {
                "answer": "I encountered an error looking up your emails. Let's try that search again in a moment.",
                "sources": [],
                "emails_found": 0,
                "retrieved_emails": [],
                "query_plan": plan.model_dump(),
            }

        email_data, retrieved_emails = self._build_email_context(emails)

        if not emails:
            return await self._generate_empty_state(question, plan)

        return await self._generate_rag_response(
            question=question,
            conversation=conversation,
            email_data=email_data,
            emails=emails,
            retrieved_emails=retrieved_emails,
            plan=plan,
        )

    def _retrieve_emails(self, search_query: str, plan: QueryPlan) -> list[Any] | None:
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
            return emails
        except Exception:
            logger.exception("Email retrieval failed.")
            return None

    def _build_email_context(
        self, emails: list[Any]
    ) -> tuple[list[tuple[Any, Any]], list[dict[str, Any]]]:
        email_data = self.retriever.load_email_data(emails)
        retrieved_emails: list[dict[str, Any]] = []

        for email, intelligence in email_data:
            extracted = (
                intelligence.extracted_data
                if intelligence and intelligence.extracted_data
                else {}
            )
            entities = extracted.get(
                "extracted_entities", extracted.get("entities", {})
            )

            retrieved_emails.append(
                {
                    "email_id": email.id,
                    "subject": email.subject,
                    "sender": email.sender,
                    "gmail_message_id": email.gmail_message_id,
                    "recipient": email.recipient,
                    "received_at": email.received_at,
                    "category": intelligence.category if intelligence else None,
                    "priority": intelligence.priority if intelligence else None,
                    "summary": intelligence.summary if intelligence else None,
                    "requires_reply": extracted.get("requires_reply", False),
                    "entities": entities,
                    "action_items": (
                        entities.get("action_items", [])
                        if isinstance(entities, dict)
                        else []
                    ),
                }
            )

        return email_data, retrieved_emails

    async def _generate_empty_state(self, question: str, plan: QueryPlan) -> dict[str, Any]:
        llm = get_llm()
        fallback_prompt = f"""
        You are INQUIREA, an AI Email Copilot. The user asked a question, but the database search filters returned 0 results.
        Analyze the user's current request and the intended filters below to formulate a helpful response confirming that no matching emails exist.
        
        USER QUESTION: "{question}"
        INTENDED FILTERS TRIGGERED:
        - Category Filter: {plan.category}
        - Priority Filter: {plan.priority}
        - Explicit Sender Filter: {plan.sender}
        - Requires Reply Mandatory: {plan.requires_reply}
        
        CRITICAL FORMATTING INSTRUCTION:
        Output ONLY the direct response to the user. Do NOT include conversational introductions or meta commentary.
        """.strip()

        try:
            response = await llm.ainvoke(fallback_prompt)
            answer = response.content if hasattr(response, "content") else str(response)
        except Exception:
            answer = "I couldn't find that information in your inbox."

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
        conversation: list[dict],
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
            response = await llm.ainvoke(prompt)
            answer = response.content if hasattr(response, "content") else str(response)
        except Exception:
            return {
                "answer": "Sorry, I ran into an error while processing your email context records.",
                "sources": [email.id for email in emails],
                "emails_found": len(emails),
                "retrieved_emails": retrieved_emails,
                "query_plan": plan.model_dump(),
            }

        return {
            "answer": str(answer),
            "sources": [email.id for email in emails],
            "emails_found": len(emails),
            "retrieved_emails": retrieved_emails,
            "query_plan": plan.model_dump(),
        }