import jwt

from fastapi import Cookie
from fastapi import HTTPException

from backend.app.core.config import get_settings


settings = get_settings()


def get_current_user(
    access_token: str | None = Cookie(
        default=None
    )
):
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    try:
        payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return {
            "user_id": int(user_id)
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )