from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import (
    get_current_user,
)
from backend.app.database.session import (
    get_db,
)
from backend.app.models.email import Email
from backend.app.models.email_intelligence import (
    EmailIntelligence,
)

router = APIRouter(
    prefix="/email-intelligence",
    tags=["Email Intelligence"],
)


@router.get("/")
def get_intelligence(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all processed email intelligence for
    the authenticated user.
    """

    return (
        db.query(EmailIntelligence)
        .join(
            Email,
            Email.id == EmailIntelligence.email_id,
        )
        .filter(
            Email.user_id == current_user["user_id"],
        )
        .order_by(
            Email.received_at.desc(),
        )
        .all()
    )


@router.get("/{email_id}")
def get_email_intelligence(
    email_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return intelligence for a single email.
    """

    return (
        db.query(EmailIntelligence)
        .join(
            Email,
            Email.id == EmailIntelligence.email_id,
        )
        .filter(
            EmailIntelligence.email_id == email_id,
        )
        .filter(
            Email.user_id == current_user["user_id"],
        )
        .first()
    )