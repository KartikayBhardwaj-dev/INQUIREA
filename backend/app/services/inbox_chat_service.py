from __future__ import annotations

import logging
import uuid

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
    - Create conversations
    - Load conversation memory
    - Persist chat history
    - Call ChatAgent
    - Return structured responses
    """

    HISTORY_LIMIT = 8

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.agent = ChatAgent(db)

    # ---------------------------------------------------------
    # Conversation Memory
    # ---------------------------------------------------------

    def _load_conversation(
        self,
        conversation_id: str,
        user_id: int,
    ) -> list[dict]:
        """
        Load the most recent conversation turns
        in chronological order.
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
            "Loaded %d conversation messages.",
            len(rows),
        )

        return [
            {
                "role": row.role,
                "message": row.message,
            }
            for row in rows
        ]

    # ---------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------

    def _save_message(
        self,
        conversation_id: str,
        user_id: int,
        role: str,
        message: str,
    ) -> None:
        """
        Persist one conversation message.
        """

        self.db.add(
            ChatHistory(
                conversation_id=conversation_id,
                user_id=user_id,
                role=role,
                message=message,
            )
        )

    # ---------------------------------------------------------
    # Main Entry Point
    # ---------------------------------------------------------

    async def chat(
        self,
        user_id: int,
        question: str,
        conversation_id: str | None = None,
    ) -> ChatResponse:
        """
        Process one AI Inbox Chat request.
        """

        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

            logger.info(
                "Created conversation %s",
                conversation_id,
            )

        conversation = self._load_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        try:

            result = await self.agent.chat(
                question=question,
                conversation=conversation,
            )

        except Exception:

            logger.exception(
                "ChatAgent execution failed."
            )
            raise

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
                message=result["answer"],
            )

            self.db.commit()

            logger.debug(
                "Conversation committed."
            )

        except Exception:

            self.db.rollback()

            logger.exception(
                "Failed to persist conversation."
            )

            raise

        return ChatResponse(
            conversation_id=conversation_id,
            answer=result["answer"],
            sources=result["sources"],
            emails_found=result["emails_found"],
            retrieved_emails=result["retrieved_emails"],
            query_plan=result["query_plan"],
        )

    # ---------------------------------------------------------
    # Conversation History
    # ---------------------------------------------------------

    def get_conversation(
        self,
        conversation_id: str,
        user_id: int,
    ) -> list[ChatHistory]:
        """
        Return a complete conversation.
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

    # ---------------------------------------------------------
    # User Conversations
    # ---------------------------------------------------------

    def list_conversations(
        self,
        user_id: int,
    ) -> list[str]:
        """
        Return every conversation owned by the user.
        """

        rows = (
            self.db.query(ChatHistory.conversation_id)
            .filter(
                ChatHistory.user_id == user_id,
            )
            .distinct()
            .all()
        )

        return [row[0] for row in rows]

    # ---------------------------------------------------------
    # Delete Conversation
    # ---------------------------------------------------------

    def delete_conversation(
        self,
        conversation_id: str,
        user_id: int,
    ) -> None:
        """
        Delete an entire conversation.
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

            logger.info(
                "Deleted conversation %s",
                conversation_id,
            )

        except Exception:

            self.db.rollback()

            logger.exception(
                "Failed to delete conversation."
            )

            raise