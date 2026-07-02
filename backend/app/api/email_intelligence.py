from fastapi import APIRouter, Depends, Request

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
from backend.app.models.users import User
from backend.app.services.email_intelligence_service import (
    EmailIntelligenceService,
)

router = APIRouter(
    prefix="/email-intelligence",
    tags=["Email Intelligence"],
)


@router.post("/process")
async def process_unprocessed_emails(
    request: Request,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):

    count = (
        await EmailIntelligenceService
        .process_all_unprocessed(
            db=db,
            request=request,
        )
    )

    return {
        "success": True,
        "processed": count,
    }


@router.get("/")
def get_intelligence(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):

    user = (
        db.query(User)
        .filter(
            User.id
            ==
            current_user["user_id"]
        )
        .first()
    )

    data = (
        db.query(
            EmailIntelligence
        )
        .join(
            Email,
            Email.id
            ==
            EmailIntelligence.email_id
        )
        .filter(
            Email.user_id
            ==
            user.id
        )
        .all()
    )

    return data


@router.get("/{email_id}")
def get_email_intelligence(

    email_id: int,

    current_user=Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    intelligence = (

        db.query(
            EmailIntelligence
        )

        .join(
            Email,
            Email.id
            ==
            EmailIntelligence.email_id
        )

        .filter(
            EmailIntelligence.email_id
            ==
            email_id
        )

        .filter(
            Email.user_id
            ==
            current_user["user_id"]
        )

        .first()

    )

    return intelligence