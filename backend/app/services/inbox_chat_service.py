from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.agents.chat_agent import ChatAgent
from backend.app.models.chat_history import ChatHistory
from backend.app.schemas.chat import ChatResponse

logger = logging.getLogger(__name__)


class InboxChatService:
    """
    Service layer for AI Inbox Chat.

    Responsibilities
    ----------------
    - Create and manage conversation sessions
    - Load conversation memory for multi-turn context
    - Persist user & assistant chat messages
    - Delegate requests to ChatAgent (handling Planner, Tool Executor, and RAG execution)
    - Return validated, structured ChatResponse schemas
    """

    HISTORY_LIMIT = 8

    def __init__(self, db: Session):
        self.db = db
        self.agent = ChatAgent(db)

    def _load_conversation(
        self,
        conversation_id: str,
        user_id: int,
    ) -> list[dict[str, str]]:
        """
        Load the most recent conversation turns in chronological order.
        """
        rows = (
            self.db.query(ChatHistory)
            .filter(
                ChatHistory.conversation_id == conversation_id,
                ChatHistory.user_id == user_id,
            )
            .order_by(ChatHistory.created_at.desc())
            .limit(self.HISTORY_LIMIT)
            .all()
        )

        rows.reverse()

        logger.debug(
            "Loaded %d conversation messages for session %s.",
            len(rows),
            conversation_id,
        )

        return [
            {
                "role": row.role,
                "message": row.message,
            }
            for row in rows
        ]

    def _save_message(
        self,
        conversation_id: str,
        user_id: int,
        role: str,
        message: str,
    ) -> None:
        """
        Persist one conversation message into database.
        """
        self.db.add(
            ChatHistory(
                conversation_id=conversation_id,
                user_id=user_id,
                role=role,
                message=message,
            )
        )

    async def chat(
        self,
        user_id: int,
        question: str,
        conversation_id: str | None = None,
    ) -> ChatResponse:
        """
        Process an incoming AI Inbox Chat request.
        
        Orchestrates session creation, context loading, tool/RAG execution via ChatAgent,
        and atomic database message persistence.
        """
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
            logger.info("Created new conversation session: %s", conversation_id)

        conversation = self._load_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        # Step 1 — Delegate to ChatAgent (Planner -> Tool / RAG)
        try:
            result: dict[str, Any] = await self.agent.chat(
                question=question,
                conversation=conversation,
                user_id=user_id,
            )
        except Exception:
            logger.exception("ChatAgent execution failed for conversation %s.", conversation_id)
            raise

        # Step 2 — Atomically Persist Conversation Turn
        try:
            self._save_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                message=question,
            )

            self._save_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                message=str(result.get("answer", "")),
            )

            self.db.commit()
            logger.debug("Conversation session %s successfully committed.", conversation_id)

        except SQLAlchemyError:
            self.db.rollback()
            logger.exception("Database transaction failed. Rolled back conversation save for %s.", conversation_id)
            raise

        # Step 3 — Construct & Return Structured Response
        return ChatResponse(
            conversation_id=conversation_id,
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            emails_found=result.get("emails_found", 0),
            retrieved_emails=result.get("retrieved_emails", []),
            query_plan=result.get("query_plan", {}),
            tool=result.get("tool"),
            tool_result=result.get("tool_result"),
        )

    def get_conversation(
        self,
        conversation_id: str,
        user_id: int,
    ) -> list[ChatHistory]:
        """
        Return the complete chronological message history for a conversation.
        """
        return (
            self.db.query(ChatHistory)
            .filter(
                ChatHistory.conversation_id == conversation_id,
                ChatHistory.user_id == user_id,
            )
            .order_by(ChatHistory.created_at.asc())
            .all()
        )

    def list_conversations(
        self,
        user_id: int,
    ) -> list[str]:
        """
        Return a list of all distinct conversation IDs owned by the user.
        """
        rows = (
            self.db.query(ChatHistory.conversation_id)
            .filter(ChatHistory.user_id == user_id)
            .distinct()
            .all()
        )
        return [row[0] for row in rows]

    def delete_conversation(
        self,
        conversation_id: str,
        user_id: int,
    ) -> None:
        """
        Delete an entire conversation history session for a given user.
        """
        try:
            (
                self.db.query(ChatHistory)
                .filter(
                    ChatHistory.conversation_id == conversation_id,
                    ChatHistory.user_id == user_id,
                )
                .delete()
            )
            self.db.commit()
            logger.info("Successfully deleted conversation session: %s", conversation_id)

        except SQLAlchemyError:
            self.db.rollback()
            logger.exception("Failed to delete conversation session %s. Transaction rolled back.", conversation_id)
            raise