from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.database.session import get_db
from backend.app.models.users import User
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
    """
    Build an authenticated Gmail service for the current user.
    """

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
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
    current_user=Depends(get_current_user),
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
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    gmail = await _get_gmail_service(
        db=db,
        user_id=current_user["user_id"],
    )

    return await gmail.get_email(
        message_id,
    )


@router.get("/thread/{thread_id}")
async def get_thread(
    thread_id: str,
    current_user=Depends(get_current_user),
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
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == current_user["user_id"])
        .first()
    )

    emails_synced = await EmailSyncService.sync_emails(
        db=db,
        user=user,
        days=days,
    )

    return {
        "success": True,
        "days": days,
        "emails_synced": emails_synced,
    }