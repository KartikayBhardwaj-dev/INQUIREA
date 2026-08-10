from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.database.session import get_db
from backend.app.models.email import Email
from backend.app.models.email_intelligence import EmailIntelligence
from backend.app.schemas.email_intelligence import (
    EmailIntelligenceResponse,
)


router = APIRouter(
    prefix="/email-intelligence",
    tags=["Email Intelligence"],
)


def _build_response(
    intelligence: EmailIntelligence,
    email: Email,
) -> EmailIntelligenceResponse:
    """
    Build the intelligence response using the local Email record.

    Important:
    - email.id is the local database ID.
    - email.gmail_message_id is the actual Gmail message ID.
    """

    return EmailIntelligenceResponse(
        id=intelligence.id,

        # Local database ID.
        email_id=intelligence.email_id,

        # Actual Gmail message ID.
        gmail_message_id=email.gmail_message_id,

        category=intelligence.category,
        priority=intelligence.priority,
        summary=intelligence.summary,
        extracted_data=intelligence.extracted_data,
        tags=intelligence.tags,
        confidence=intelligence.confidence,
        processed_at=intelligence.processed_at,

        sender=email.sender,
        recipient=email.recipient,
        subject=email.subject,
        snippet=email.snippet,
        received_at=email.received_at,
    )


@router.get(
    "/",
    response_model=list[EmailIntelligenceResponse],
)
def get_intelligence(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return processed email intelligence together
    with the corresponding email metadata.

    EmailIntelligence.email_id points to Email.id.

    The Gmail API, however, requires
    Email.gmail_message_id.
    """

    rows = (
        db.query(
            EmailIntelligence,
            Email,
        )
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

    return [
        _build_response(
            intelligence,
            email,
        )
        for intelligence, email in rows
    ]


@router.get(
    "/{email_id}",
    response_model=EmailIntelligenceResponse | None,
)
def get_email_intelligence(
    email_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return intelligence for a single local email.

    `email_id` here is the LOCAL Email.id.

    The response additionally contains
    `gmail_message_id`, which should be used
    when communicating with Gmail.
    """

    row = (
        db.query(
            EmailIntelligence,
            Email,
        )
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

    if not row:
        return None

    intelligence, email = row

    return _build_response(
        intelligence,
        email,
    )