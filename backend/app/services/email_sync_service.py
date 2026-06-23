import base64
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from backend.app.models.email import Email
from backend.app.models.users import User
from backend.app.services.gmail_service import GmailService
from backend.app.services.google_token_service import (
    GoogleTokenService,
)


class EmailSyncService:

    MAX_EMAIL_LENGTH = 4000

    @staticmethod
    async def sync_emails(
        db: Session,
        user: User,
        days: int = 7,
    ) -> int:

        access_token = (
            await GoogleTokenService.refresh_access_token(
                user=user,
                db=db,
            )
        )

        gmail = GmailService(
            access_token=access_token
        )

        result = await gmail.list_emails(
            query=f"newer_than:{days}d",
            max_results=100,
        )

        messages = result.get(
            "messages",
            []
        )

        saved_count = 0

        for message in messages:

            gmail_message_id = message["id"]

            existing = (
                db.query(Email)
                .filter(
                    Email.gmail_message_id
                    == gmail_message_id
                )
                .first()
            )

            if existing:
                continue

            message_data = (
                await gmail.get_email(
                    gmail_message_id
                )
            )

            email = (
                EmailSyncService
                ._build_email_model(
                    user_id=user.id,
                    message_data=message_data,
                )
            )

            db.add(email)

            saved_count += 1

        db.commit()

        return saved_count

    @staticmethod
    def _clean_email_body(
        body: str,
    ) -> str:

        if not body:
            return ""

        try:

            if "<html" in body.lower():

                soup = BeautifulSoup(
                    body,
                    "html.parser",
                )

                body = soup.get_text(
                    separator=" ",
                    strip=True,
                )

        except Exception:
            pass

        return body[:EmailSyncService.MAX_EMAIL_LENGTH]

    @staticmethod
    def _build_email_model(
        user_id: int,
        message_data: dict,
    ) -> Email:

        payload = message_data.get(
            "payload",
            {}
        )

        headers = {
            h["name"]: h["value"]
            for h in payload.get(
                "headers",
                []
            )
        }

        sender = headers.get(
            "From",
            ""
        )

        recipient = headers.get(
            "To",
            ""
        )

        subject = headers.get(
            "Subject",
            ""
        )

        received_at = None

        try:

            if headers.get("Date"):

                received_at = (
                    parsedate_to_datetime(
                        headers["Date"]
                    )
                )

        except Exception:
            pass

        body = (
            EmailSyncService
            ._extract_body(payload)
        )

        body = (
            EmailSyncService
            ._clean_email_body(body)
        )

        return Email(
            user_id=user_id,
            gmail_message_id=message_data["id"],
            gmail_thread_id=message_data["threadId"],
            sender=sender,
            recipient=recipient,
            subject=subject,
            snippet=message_data.get(
                "snippet",
                ""
            ),
            body=body,
            label_ids=",".join(
                message_data.get(
                    "labelIds",
                    []
                )
            ),
            received_at=received_at,
            is_processed=False,
        )

    @staticmethod
    def _extract_body(
        payload: dict,
    ) -> str:

        body_data = (
            payload.get(
                "body",
                {}
            ).get("data")
        )

        if body_data:

            try:

                return (
                    base64.urlsafe_b64decode(
                        body_data
                    )
                    .decode(
                        "utf-8",
                        errors="ignore"
                    )
                )

            except Exception:
                return ""

        for part in payload.get(
            "parts",
            []
        ):

            mime_type = part.get(
                "mimeType"
            )

            if mime_type in (
                "text/plain",
                "text/html",
            ):

                data = (
                    part.get(
                        "body",
                        {}
                    ).get("data")
                )

                if not data:
                    continue

                try:

                    return (
                        base64.urlsafe_b64decode(
                            data
                        )
                        .decode(
                            "utf-8",
                            errors="ignore"
                        )
                    )

                except Exception:
                    continue

        return ""