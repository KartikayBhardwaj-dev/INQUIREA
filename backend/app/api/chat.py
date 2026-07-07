from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import (
    get_current_user,
)
from backend.app.database.session import (
    SessionLocal,
)
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationHistory,
)
from backend.app.services.inbox_chat_service import (
    InboxChatService,
)

router = APIRouter(
    prefix="/chat",
    tags=["AI Inbox Chat"],
)


# ---------------------------------------------------------
# Database Dependency
# ---------------------------------------------------------


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# Start New Conversation
# ---------------------------------------------------------


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = InboxChatService(db)

    return await service.chat(
    user_id=current_user["user_id"],
    question=request.message,
    conversation_id=request.conversation_id,
)


# ---------------------------------------------------------
# Continue Conversation
# ---------------------------------------------------------


@router.post(
    "/{conversation_id}",
    response_model=ChatResponse,
)
async def continue_chat(
    conversation_id: str,
    request: ChatRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = InboxChatService(db)

    return await service.chat(
    user_id=current_user["user_id"],
    question=request.message,
    conversation_id=conversation_id,
)


# ---------------------------------------------------------
# Conversation History
# ---------------------------------------------------------


@router.get(
    "/history/{conversation_id}",
    response_model=ConversationHistory,
)
def conversation_history(
    conversation_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = InboxChatService(db)

    messages = service.get_conversation(
        conversation_id=conversation_id,
        user_id=current_user["user_id"],
    )

    return ConversationHistory(
        conversation_id=conversation_id,
        messages=messages,
    )


# ---------------------------------------------------------
# List Conversations
# ---------------------------------------------------------


@router.get(
    "/conversations",
)
def conversations(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = InboxChatService(db)

    return {
        "conversations": service.list_conversations(
            user_id=current_user["user_id"],
        )
    }