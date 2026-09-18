from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.auth.jwt import create_access_token
from backend.app.auth.oauth import oauth
from backend.app.schemas.auth import UserResponse
from backend.app.database.session import get_db
from backend.app.models.users import User
from backend.app.auth.dependencies import get_current_user

settings = get_settings()

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
    )


@router.get(
    "/google/callback",
    name="google_callback",
)
async def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    token = await oauth.google.authorize_access_token(request)

    user_info = token["userinfo"]

    google_id = user_info["sub"]

    user = (
        db.query(User)
        .filter(User.google_id == google_id)
        .first()
    )

    if not user:
        user = User(
            email=user_info["email"],
            google_id=google_id,
            full_name=user_info.get("name"),
            profile_picture=user_info.get("picture"),
        )

        db.add(user)

    user.google_access_token = token.get("access_token")

    # Google may not return a refresh token on every login.
    # Never overwrite an existing refresh token with None.
    refresh_token = token.get("refresh_token")

    if refresh_token:
        user.google_refresh_token = refresh_token

    user.google_token_expiry = datetime.utcfromtimestamp(
        token["expires_at"]
    )

    user.last_login_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.id)

    response = RedirectResponse(
        url=f"{settings.FRONTEND_URL}/dashboard",
        status_code=303,
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="none" if settings.APP_ENV == "production" else "lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return response


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == current_user["user_id"])
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


@router.post("/logout")
def logout():
    response = Response(content="Logged out")

    response.delete_cookie(
        key="access_token",
        secure=settings.APP_ENV == "production",
        samesite="none" if settings.APP_ENV == "production" else "lax",
    )

    return response