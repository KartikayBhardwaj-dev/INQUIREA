from datetime import datetime
from datetime import timedelta

import jwt

from backend.app.core.config import get_settings

settings = get_settings()


def create_access_token(user_id: int):

    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256"
    )