from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request

from sqlalchemy.orm import Session

from backend.app.auth.jwt import create_access_token
from backend.app.auth.oauth import oauth

from backend.app.database.session import get_db

from backend.app.models.users import User
from backend.app.auth.dependencies import (
    get_current_user
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.get("/google/login")
async def google_login(
    request: Request
):
    redirect_uri = request.url_for(
        "google_callback"
    )

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )


@router.get(
    "/google/callback",
    name="google_callback"
)
async def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):

    token = await oauth.google.authorize_access_token(
        request
    )

    user_info = token["userinfo"]

    google_id = user_info["sub"]

    user = (
        db.query(User)
        .filter(
            User.google_id == google_id
        )
        .first()
    )

    if not user:

        user = User(
            email=user_info["email"],
            google_id=google_id,
            full_name=user_info.get("name"),
            profile_picture=user_info.get(
                "picture"
            )
        )

        db.add(user)

    user.google_access_token = token.get(
        "access_token"
    )

    user.google_refresh_token = token.get(
        "refresh_token"
    )

    user.google_token_expiry = datetime.utcfromtimestamp(
        token["expires_at"]
    )

    user.last_login_at = datetime.utcnow()

    db.commit()

    db.refresh(user)

    access_token = create_access_token(
        user.id
    )

    return {
        "access_token": access_token,
        "user": {
            "id": user.id,
            "email": user.email
        }
    }





@router.get("/me")
def me(
    user=Depends(get_current_user)
):
    return user