# from __future__ import annotations

# import logging

# from sqlalchemy.orm import Session

# from backend.app.core.llm import get_llm
# from backend.app.services.chat_prompt_builder import ChatPromptBuilder
# from backend.app.services.chat_retriever import ChatRetriever
# from backend.app.services.query_planner import QueryPlanner

# logger = logging.getLogger(__name__)


# class ChatAgent:
#     """
#     AI Inbox Chat Agent.

#     Responsibilities
#     ----------------
#     - Understand the user's question
#     - Build a retrieval plan
#     - Retrieve relevant emails
#     - Build the production RAG prompt
#     - Invoke the LLM
#     - Return a structured response

#     This class orchestrates the complete Level 1
#     AI Inbox Chat pipeline.
#     """

#     def __init__(
#         self,
#         db: Session,
#     ):
#         self.db = db
#         self.retriever = ChatRetriever(db)
#         self.planner = QueryPlanner()

#     async def chat(
#         self,
#         question: str,
#         conversation: list[dict] | None = None,
#     ) -> dict:
#         """
#         Execute the complete AI Inbox Chat pipeline.

#         Pipeline
#         --------
#         Question
#             ↓
#         Query Planner
#             ↓
#         Retriever
#             ↓
#         Prompt Builder
#             ↓
#         LLM
#             ↓
#         Structured Response
#         """

#         conversation = conversation or []

#         logger.info(
#             "Processing chat question: %s",
#             question,
#         )

#         # ---------------------------------------------------------
#         # Step 1 — Query Planning
#         # ---------------------------------------------------------

#         try:

#             plan = await self.planner.plan(
#                 question=question,
#             )

#         except Exception:

#             logger.exception(
#                 "Query planner failed.",
#             )
#             raise

#         logger.info(
#             "Query plan generated: %s",
#             plan.model_dump(),
#         )

#         # ---------------------------------------------------------
#         # Step 2 — Determine Search Query
#         # ---------------------------------------------------------

#         search_query = (
#             plan.semantic_query
#             or question
#         )

#         logger.debug(
#             "Semantic query: %s",
#             search_query,
#         )

#         # ---------------------------------------------------------
#         # Step 3 — Retrieve Emails
#         # ---------------------------------------------------------

#         try:

#             emails = self.retriever.retrieve(
#                 query=search_query,
#                 limit=plan.retrieve_limit,
#                 category=plan.category,
#                 priority=plan.priority,
#                 sender=plan.sender,
#                 requires_reply=plan.requires_reply,
#                 sort_by=plan.sort_by,
#                 date_from=plan.date_from,
#                 date_to=plan.date_to,
#             )

#         except Exception:

#             logger.exception(
#                 "Email retrieval failed.",
#             )
#             raise

#         logger.info(
#             "Retrieved %d email(s).",
#             len(emails),
#         )

#         logger.debug(
#             "Retrieved IDs: %s",
#             [email.id for email in emails],
#         )

#         # ---------------------------------------------------------
#         # Step 4 — Load Email Intelligence
#         # ---------------------------------------------------------

#         email_data = self.retriever.load_email_data(
#             emails,
#         )

#         logger.debug(
#             "Loaded intelligence for %d email(s).",
#             len(email_data),
#         )

#         # ---------------------------------------------------------
#         # Build Retrieved Email Metadata
#         # ---------------------------------------------------------

#         retrieved_emails: list[dict] = []

#         for email, intelligence in email_data:

#             extracted = (
#         intelligence.extracted_data
#         if intelligence and intelligence.extracted_data
#         else {}
#     )

#             entities = extracted.get(

#     "extracted_entities",

#     {},

# )
#             retrieved_emails.append(
#         {
#             "email_id": email.id,
#             "subject": email.subject,
#             "sender": email.sender,
#             "recipient": email.recipient,
#             "received_at": email.received_at,

#             "category": (
#                 intelligence.category
#                 if intelligence
#                 else None
#             ),

#             "priority": (
#                 intelligence.priority
#                 if intelligence
#                 else None
#             ),

#             "summary": (
#                 intelligence.summary
#                 if intelligence
#                 else None
#             ),

#             "requires_reply": extracted.get(
#                 "requires_reply",
#                 False,
#             ),

#              "entities": entities,

#             "action_items": entities.get(

#             "action_items",

#             [],
#             ),
#         }
#     )

#                 # ---------------------------------------------------------
#         # Step 5 — Handle Empty Retrieval
#         # ---------------------------------------------------------

#         if not emails:

#             logger.info(
#                 "No matching emails found.",
#             )

#             return {
#                 "answer": (
#                     "I couldn't find that information "
#                     "in your inbox."
#                 ),
#                 "sources": [],
#                 "emails_found": 0,
#                 "retrieved_emails": [],
#                 "query_plan": plan.model_dump(),
#             }

#         # ---------------------------------------------------------
#         # Step 6 — Build Production RAG Prompt
#         # ---------------------------------------------------------

#         prompt = ChatPromptBuilder.build_prompt(
#             question=question,
#             conversation=conversation,
#             email_data=email_data,
#         )

#         logger.debug(
#             "Prompt successfully built.",
#         )

#         # ---------------------------------------------------------
#         # Step 7 — Invoke LLM
#         # ---------------------------------------------------------

#         llm = get_llm()

#         try:

#             response = await llm.ainvoke(
#                 prompt,
#             )

#             answer = (
#                 response.content
#                 if hasattr(response, "content")
#                 else str(response)
#             )

#         except Exception:

#             logger.exception(
#                 "LLM invocation failed.",
#             )

#             return {
#                 "answer": (
#                     "Sorry, I couldn't process your "
#                     "request right now."
#                 ),
#                 "sources": [
#                     email.id
#                     for email in emails
#                 ],
#                 "emails_found": len(emails),
#                 "retrieved_emails": retrieved_emails,
#                 "query_plan": plan.model_dump(),
#             }

#         logger.info(
#             "LLM response generated successfully.",
#         )

#         # ---------------------------------------------------------
#         # Step 8 — Return Structured Response
#         # ---------------------------------------------------------

#         return {
#             "answer": answer,
#             "sources": [
#                 email.id
#                 for email in emails
#             ],
#             "emails_found": len(emails),
#             "retrieved_emails": retrieved_emails,
#             "query_plan": plan.model_dump(),
#         }
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
    Orchestrates the complete Level 1 AI Inbox Chat pipeline.
    """

    def __init__(self, db: Session):
        self.db = db
        self.retriever = ChatRetriever(db)
        self.planner = QueryPlanner()

    async def chat(self, question: str, conversation: list[dict] | None = None) -> dict:
        conversation = conversation or []

        logger.info("Processing chat question: %s", question)

        # ---------------------------------------------------------
        # Step 1 — Query Planning (Injected conversation tracking context)
        # ---------------------------------------------------------
        try:
            plan = await self.planner.plan(
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

        # ---------------------------------------------------------
        # Step 2 — Determine Search Query
        # ---------------------------------------------------------
        search_query = plan.semantic_query or question
        logger.debug("Semantic query: %s", search_query)

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
            logger.exception("Email retrieval failed.")
            return {
                "answer": "I encountered an error looking up your emails. Let's try that search again in a moment.",
                "sources": [],
                "emails_found": 0,
                "retrieved_emails": [],
                "query_plan": plan.model_dump(),
            }

        logger.info("Retrieved %d email(s).", len(emails))

        # ---------------------------------------------------------
        # Step 4 — Load Email Intelligence & Build Context
        # ---------------------------------------------------------
        email_data = self.retriever.load_email_data(emails)
        retrieved_emails: list[dict] = []

        for email, intelligence in email_data:
            extracted = intelligence.extracted_data if intelligence and intelligence.extracted_data else {}
            entities = extracted.get("extracted_entities", extracted.get("entities", {}))

            retrieved_emails.append(
                {
                    "email_id": email.id,
                    "subject": email.subject,
                    "sender": email.sender,
                    "recipient": email.recipient,
                    "received_at": email.received_at,
                    "category": intelligence.category if intelligence else None,
                    "priority": intelligence.priority if intelligence else None,
                    "summary": intelligence.summary if intelligence else None,
                    "requires_reply": extracted.get("requires_reply", False),
                    "entities": entities,
                    "action_items": entities.get("action_items", []) if isinstance(entities, dict) else [],
                }
            )

        # ---------------------------------------------------------
        # Step 5 — Handle Empty Retrieval (Dynamic LLM Fallback Engine)
        # ---------------------------------------------------------
        if not emails:
            logger.info("No matching emails found. Triggering dynamic empty-state agent evaluation.")
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
            Output ONLY the direct response to the user. 
            Do NOT include conversational introductions, behind-the-scenes thoughts, meta-commentary, introductory phrases like "Here is the response:", or any reasoning. Speak directly to the user.
            
            INSTRUCTIONS:
            1. If the user asked a confirmation question (e.g., "what needs a reply?", "any high priority updates?"), answer politely explaining that they are all caught up or that no emails match those specific filters right now.
            2. If the user asked for out-of-bounds metrics (e.g., weather, cooking recipes) or items completely missing from their history, reply exactly: "I couldn't find that information in your inbox."
            3. Keep the voice natural, short, and highly accurate to the filters.
            """.strip()
            
            try:
                response = await llm.ainvoke(fallback_prompt)
                answer = response.content if hasattr(response, "content") else str(response)
            except Exception:
                logger.exception("Fallback LLM invocation failed.")
                answer = "I couldn't find that information in your inbox."

            return {
                "answer": answer.strip(),
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

        # ---------------------------------------------------------
        # Step 7 — Invoke LLM
        # ---------------------------------------------------------
        llm = get_llm()
        try:
            response = await llm.ainvoke(prompt)
            answer = response.content if hasattr(response, "content") else str(response)
        except Exception:
            logger.exception("LLM invocation failed.")
            return {
                "answer": "Sorry, I ran into an error while processing your email context records.",
                "sources": [email.id for email in emails],
                "emails_found": len(emails),
                "retrieved_emails": retrieved_emails,
                "query_plan": plan.model_dump(),
            }

        return {
            "answer": answer,
            "sources": [email.id for email in emails],
            "emails_found": len(emails),
            "retrieved_emails": retrieved_emails,
            "query_plan": plan.model_dump(),
        }