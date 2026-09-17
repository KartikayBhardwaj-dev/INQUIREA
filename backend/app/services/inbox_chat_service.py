from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import logging
import uuid
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.agents.chat_agent import ChatAgent
from backend.app.models.chat_history import ChatHistory
from backend.app.schemas.chat import ChatResponse

logger = logging.getLogger(__name__)


def _make_json_serializable(obj: Any) -> Any:
    """
    Recursively convert datetimes, UUIDs, Decimals, Pydantic models, 
    and other non-serializable objects into JSON-friendly primitives.
    """
    if isinstance(obj, dict):
        return {str(k): _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [_make_json_serializable(v) for v in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, "model_dump") and callable(obj.model_dump):  # Pydantic v2
        return _make_json_serializable(obj.model_dump())
    elif hasattr(obj, "dict") and callable(obj.dict):  # Pydantic v1
        return _make_json_serializable(obj.dict())
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # Ultimate fallback to string representation to guarantee no crash
        return str(obj)


class InboxChatService:
    """
    Service layer for AI Inbox Chat.

    Responsibilities
    ----------------
    - Create and manage conversation sessions
    - Load conversation memory
    - Preserve structured action metadata
    - Persist user and assistant messages
    - Delegate execution to ChatAgent
    - Return validated ChatResponse objects
    """

    HISTORY_LIMIT = 20

    def __init__(self, db: Session):
        self.db = db
        self.agent = ChatAgent(db)

    def _load_conversation(
        self,
        conversation_id: str,
        user_id: int,
    ) -> list[dict[str, Any]]:
        """
        Load recent conversation turns.

        Besides the human-readable message, structured metadata is
        returned so the planner can resolve references such as:

            "it"
            "this draft"
            "make it shorter"
            "approve it"
            "send it"
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

        conversation: list[dict[str, Any]] = []

        for row in rows:
            conversation.append(
                {
                    "role": row.role,
                    "message": row.message,
                    "metadata": row.message_metadata or {},
                }
            )

        return conversation

    def _save_message(
        self,
        conversation_id: str,
        user_id: int,
        role: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Persist one conversation message.

        Metadata is optional and is primarily used for assistant
        action/tool state.
        """

        self.db.add(
            ChatHistory(
                conversation_id=conversation_id,
                user_id=user_id,
                role=role,
                message=message,
                message_metadata=metadata or {},
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
        """

        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

            logger.info(
                "Created new conversation session: %s",
                conversation_id,
            )

        # --------------------------------------------------
        # Load structured conversation context
        # --------------------------------------------------

        conversation = self._load_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        # --------------------------------------------------
        # Agent execution
        # --------------------------------------------------

        try:
            result: dict[str, Any] = await self.agent.chat(
                question=question,
                conversation=conversation,
                user_id=user_id,
            )

        except Exception:
            logger.exception(
                "ChatAgent execution failed for conversation %s.",
                conversation_id,
            )
            raise

        # --------------------------------------------------
        # Extract structured action metadata
        # --------------------------------------------------

        action_metadata = result.get("context_metadata") or {}

        if not isinstance(action_metadata, dict):
            action_metadata = {}

        # Always preserve tool
        tool_name = result.get("tool")
        if tool_name:
            action_metadata["tool"] = tool_name
            action_metadata["action"] = tool_name

        # Preserve complete tool result
        tool_result = result.get("tool_result")
        if isinstance(tool_result, dict):
            action_metadata["tool_result"] = tool_result

            if tool_result.get("draft_id") is not None:
                action_metadata["draft_id"] = tool_result["draft_id"]

            if tool_result.get("email_id") is not None:
                action_metadata["email_id"] = tool_result["email_id"]

            if tool_result.get("approval_status") is not None:
                action_metadata["approval_status"] = tool_result["approval_status"]

        # Preserve query plan for debugging / audit
        query_plan = result.get("query_plan")
        if isinstance(query_plan, dict):
            action_metadata["query_plan"] = query_plan

        # Preserve retrieved emails for history rendering
        retrieved_emails = result.get("retrieved_emails")
        if retrieved_emails:
            action_metadata["retrieved_emails"] = retrieved_emails

        # --------------------------------------------------
        # Persist conversation turn
        # --------------------------------------------------

        try:
            # Ensure all metadata values (including nested datetimes) are JSON serializable
            safe_action_metadata = _make_json_serializable(action_metadata)

            self._save_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                message=question,
                metadata={},
            )

            self._save_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                message=str(result.get("answer", "")),
                metadata=safe_action_metadata,
            )

            self.db.commit()

            logger.debug(
                "Conversation session %s successfully committed.",
                conversation_id,
            )

        except SQLAlchemyError:
            self.db.rollback()

            logger.exception(
                "Database transaction failed. "
                "Rolled back conversation save for %s.",
                conversation_id,
            )

            raise

        # --------------------------------------------------
        # Construct final ChatResponse
        # --------------------------------------------------

        return ChatResponse(
            conversation_id=conversation_id,
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            emails_found=result.get("emails_found", 0),
            retrieved_emails=result.get(
                "retrieved_emails",
                [],
            ),
            query_plan=result.get(
                "query_plan",
                {},
            ),
            tool=result.get("tool"),
            tool_result=result.get("tool_result"),
            error=result.get("error"),
        )

    def get_conversation(
        self,
        conversation_id: str,
        user_id: int,
    ) -> list[Any]:
        """
        Return complete chronological conversation history with metadata unpacked.
        """
        rows = (
            self.db.query(ChatHistory)
            .filter(
                ChatHistory.conversation_id == conversation_id,
                ChatHistory.user_id == user_id,
            )
            .order_by(ChatHistory.created_at.asc())
            .all()
        )

        result = []
        for row in rows:
            metadata = row.message_metadata or {}
            result.append({
                "id": row.id,
                "role": row.role,
                "content": row.message,
                "created_at": row.created_at,
                "retrieved_emails": metadata.get("retrieved_emails", []),
                "tool": metadata.get("tool"),
                "tool_result": metadata.get("tool_result"),
                "query_plan": metadata.get("query_plan", {}),
                "error": metadata.get("error"),
            })
        return result

    def list_conversations(
        self,
        user_id: int,
    ) -> list[str]:
        """
        Return all distinct conversation IDs owned by the user.
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

    def delete_conversation(
        self,
        conversation_id: str,
        user_id: int,
    ) -> None:
        """
        Delete an entire conversation history session.
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
                "Successfully deleted conversation session: %s",
                conversation_id,
            )

        except SQLAlchemyError:
            self.db.rollback()

            logger.exception(
                "Failed to delete conversation session %s. "
                "Transaction rolled back.",
                conversation_id,
            )

            raise
