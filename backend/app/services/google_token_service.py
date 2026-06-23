from datetime import datetime
from datetime import timedelta

import httpx
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.users import User

settings = get_settings()


class GoogleTokenService:

    @staticmethod
    async def refresh_access_token(
        user: User,
        db: Session,
    ) -> str:

        if (
            user.google_token_expiry
            and user.google_token_expiry > datetime.utcnow()
        ):
            return user.google_access_token

        async with httpx.AsyncClient() as client:

            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "refresh_token": user.google_refresh_token,
                    "grant_type": "refresh_token",
                },
            )

        response.raise_for_status()

        token_data = response.json()

        user.google_access_token = token_data["access_token"]

        expires_in = token_data.get(
            "expires_in",
            3600,
        )

        user.google_token_expiry = (
            datetime.utcnow()
            + timedelta(seconds=expires_in)
        )

        db.commit()

        db.refresh(user)

        return user.google_access_token