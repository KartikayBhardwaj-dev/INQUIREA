from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.database.session import get_db
from backend.app.models.users import User
from backend.app.models.email import Email
from backend.app.models.email_intelligence import EmailIntelligence
from backend.app.services.email_sync_service import (
    EmailSyncService,
)
from backend.app.services.gmail_service import GmailService
from backend.app.services.google_token_service import (
    GoogleTokenService,
)


router = APIRouter(
    prefix="/gmail",
    tags=["Gmail"],
)


async def _get_gmail_service(
    *,
    db: Session,
    user_id: int,
) -> GmailService:

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    access_token = (
        await GoogleTokenService.refresh_access_token(
            user=user,
            db=db,
        )
    )

    return GmailService(
        access_token=access_token,
    )


@router.get("/emails")
async def list_emails(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    gmail = await _get_gmail_service(
        db=db,
        user_id=current_user["user_id"],
    )

    return await gmail.list_emails(
        max_results=20,
    )


@router.get("/email/{message_id}")
async def get_email(
    message_id: str,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    user_id = current_user["user_id"]

    # --------------------------------------------------
    # 1. Find the local email
    # --------------------------------------------------

    email = (
        db.query(Email)
        .filter(
            Email.gmail_message_id
            == message_id
        )
        .filter(
            Email.user_id
            == user_id
        )
        .first()
    )

    if not email:
        raise HTTPException(
            status_code=404,
            detail="Email not found",
        )


    # --------------------------------------------------
    # 2. Find email intelligence
    # --------------------------------------------------

    intelligence = (
        db.query(
            EmailIntelligence
        )
        .filter(
            EmailIntelligence.email_id
            == email.id
        )
        .first()
    )


    # --------------------------------------------------
    # 3. Create Gmail service
    # --------------------------------------------------

    gmail = await _get_gmail_service(
        db=db,
        user_id=user_id,
    )


    # --------------------------------------------------
    # 4. Fetch complete Gmail message
    # --------------------------------------------------

    gmail_message = (
        await gmail.get_email(
            message_id
        )
    )


    # --------------------------------------------------
    # 5. Extract complete email body
    # --------------------------------------------------

    body = GmailService._extract_body(
        gmail_message.get(
            "payload"
        )
    )


    # --------------------------------------------------
    # 6. Return normalized email
    # --------------------------------------------------

    return {
        "email": {
            # Database identifiers
            "email_id": email.id,
            "gmail_message_id": (
                email.gmail_message_id
            ),
            "gmail_thread_id": (
                email.gmail_thread_id
            ),

            # Email metadata
            "sender": email.sender,
            "recipient": email.recipient,
            "subject": email.subject,
            "snippet": email.snippet,
            "received_at": email.received_at,

            # Complete Gmail body
            

            # Gmail labels
            "label_ids": (
                email.label_ids
            ),

            # Intelligence
            "priority": (
                intelligence.priority
                if intelligence
                else "normal"
            ),

            "category": (
                intelligence.category
                if intelligence
                else "other"
            ),

            "summary": (
                intelligence.summary
                if intelligence
                else ""
            ),

            "extracted_data": (
                intelligence.extracted_data
                if intelligence
                else None
            ),

            "tags": (
                intelligence.tags
                if intelligence
                else []
            ),

            "confidence": (
                intelligence.confidence
                if intelligence
                else None
            ),

            "requires_reply": (
                getattr(
                    intelligence,
                    "requires_reply",
                    False,
                )
                if intelligence
                else False
            ),

            "processed_at": (
                intelligence.processed_at
                if intelligence
                else None
            ),
        }
    }


@router.get("/thread/{thread_id}")
async def get_thread(
    thread_id: str,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    gmail = await _get_gmail_service(
        db=db,
        user_id=current_user["user_id"],
    )

    return await gmail.get_thread(
        thread_id,
    )


@router.post("/sync")
async def sync_emails(
    days: int = 7,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    user = (
        db.query(User)
        .filter(
            User.id
            == current_user["user_id"]
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    emails_synced = (
        await EmailSyncService.sync_emails(
            db=db,
            user=user,
            days=days,
        )
    )

    return {
        "success": True,
        "days": days,
        "emails_synced": emails_synced,
    }