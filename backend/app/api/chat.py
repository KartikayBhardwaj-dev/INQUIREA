from __future__ import annotations

import logging
from typing import Any, Generator

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.database.session import SessionLocal
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationHistory,
)
from backend.app.services.inbox_chat_service import InboxChatService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["AI Inbox Chat"],
)


# ---------------------------------------------------------
# Database Dependency
# ---------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session for API endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# Start or Continue Chat Session
# ---------------------------------------------------------

@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Process an AI Inbox Chat message",
    description="Main chat entry point. Routes user questions through QueryPlanner to either Level 1 Hybrid Search or Level 2 Tool Execution.",
)
async def chat(
    request: ChatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Process a new or ongoing chat request using request body parameters."""
    service = InboxChatService(db)

    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        return await service.chat(
            user_id=user_id,
            question=request.message,
            conversation_id=request.conversation_id,
        )
    except Exception as exc:
        logger.exception("Error processing chat request for user %s", current_user)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing your chat request.",
        ) from exc


@router.post(
    "/{conversation_id}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Continue an existing Chat Session by ID",
)
async def continue_chat(
    conversation_id: str,
    request: ChatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Continue an existing conversation session via URL path parameter overriding."""
    service = InboxChatService(db)

    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        return await service.chat(
            user_id=user_id,
            question=request.message,
            conversation_id=conversation_id,
        )
    except Exception as exc:
        logger.exception("Error continuing chat session %s", conversation_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while continuing conversation '{conversation_id}'.",
        ) from exc


# ---------------------------------------------------------
# Conversation History Management
# ---------------------------------------------------------

@router.get(
    "/history/{conversation_id}",
    response_model=ConversationHistory,
    status_code=status.HTTP_200_OK,
    summary="Retrieve full conversation message history",
)
async def conversation_history(
    conversation_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationHistory:
    """Return all historical chat turns for a given conversation session."""
    service = InboxChatService(db)
    user_id = current_user.get("user_id") or current_user.get("id")

    messages = service.get_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    return ConversationHistory(
        conversation_id=conversation_id,
        messages=messages,
    )


@router.get(
    "/conversations",
    response_model=list[str],
    status_code=status.HTTP_200_OK,
    summary="List all conversation IDs owned by user",
)
async def conversations(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[str]:
    """List unique conversation session IDs created by the active user."""
    service = InboxChatService(db)
    user_id = current_user.get("user_id") or current_user.get("id")

    return service.list_conversations(user_id=user_id)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an entire conversation session",
)
async def delete_conversation(
    conversation_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Delete a conversation history session and all associated messages."""
    service = InboxChatService(db)
    user_id = current_user.get("user_id") or current_user.get("id")

    try:
        service.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": f"Successfully deleted conversation {conversation_id}.",
        }
    except Exception as exc:
        logger.exception("Failed to delete conversation session %s", conversation_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete conversation '{conversation_id}'.",
        ) from exc