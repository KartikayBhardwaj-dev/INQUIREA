from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from backend.app.agents.chat_agent import ChatAgent
from backend.app.models.chat_history import ChatHistory
from backend.app.schemas.chat import ChatResponse


class InboxChatService:
    """
    Service layer for AI Inbox Chat.

    Responsibilities
    ----------------
    - Manage conversations
    - Persist chat history
    - Retrieve conversation memory
    - Call ChatAgent
    - Return structured responses
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.agent = ChatAgent(db)

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
        Process one inbox chat request.
        """

        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        # -----------------------------------------------------
        # Load previous conversation (Step 12)
        # -----------------------------------------------------

        history_rows = (
            self.db.query(ChatHistory)
            .filter(
                ChatHistory.conversation_id == conversation_id,
                ChatHistory.user_id == user_id,
            )
            .order_by(ChatHistory.created_at.desc())
            .limit(8)
            .all()
        )

        history_rows.reverse()

        conversation = [
            {
                "role": row.role,
                "message": row.message,
            }
            for row in history_rows
        ]

        # -----------------------------------------------------
        # Call Chat Agent
        # -----------------------------------------------------

        result = await self.agent.chat(
            question=question,
            conversation=conversation,
        )

        # -----------------------------------------------------
        # Persist User Message
        # -----------------------------------------------------

        self.db.add(
            ChatHistory(
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                message=question,
            )
        )

        # -----------------------------------------------------
        # Persist Assistant Message
        # -----------------------------------------------------

        self.db.add(
            ChatHistory(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                message=result["answer"],
            )
        )

        self.db.commit()

        # -----------------------------------------------------
        # API Response (Step 14)
        # -----------------------------------------------------

        return ChatResponse(
            conversation_id=conversation_id,
            answer=result["answer"],
            sources=result["emails"],
            emails_found=len(result["emails"]),
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
        Return all messages in a conversation.
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
        Return all conversation IDs for a user.
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

        (
            self.db.query(ChatHistory)
            .filter(
                ChatHistory.conversation_id == conversation_id,
                ChatHistory.user_id == user_id,
            )
            .delete()
        )

        self.db.commit()