import base64
import logging
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from backend.app.models.email import Email
from backend.app.models.users import User
from backend.app.services.gmail_service import GmailService
from backend.app.services.google_token_service import (
    GoogleTokenService,
)
from backend.app.tasks.email_tasks import (
    process_email,
)

logger = logging.getLogger(__name__)


class EmailSyncService:
    """
    Synchronizes Gmail messages into PostgreSQL.

    New emails are persisted and automatically queued for
    intelligence processing via Celery.
    """

    MAX_EMAIL_LENGTH = 4000
    MAX_SYNC_EMAILS = 100

    @staticmethod
    async def sync_emails(
        db: Session,
        user: User,
        days: int = 7,
    ) -> int:
        """
        Synchronize recent Gmail messages.

        Only previously unseen emails are inserted.
        Each newly inserted email is queued for background
        intelligence processing.
        """

        access_token = (
            await GoogleTokenService.refresh_access_token(
                user=user,
                db=db,
            )
        )

        gmail = GmailService(
            access_token=access_token,
        )

        result = await gmail.list_emails(
            query=f"newer_than:{days}d",
            max_results=EmailSyncService.MAX_SYNC_EMAILS,
        )

        messages = result.get(
            "messages",
            [],
        )

        logger.info(
            "Fetched %s Gmail messages.",
            len(messages),
        )

        if not messages:
            return 0

        gmail_ids = [
            message["id"]
            for message in messages
        ]

        existing_ids = {
            row[0]
            for row in (
                db.query(
                    Email.gmail_message_id,
                )
                .filter(
                    Email.gmail_message_id.in_(
                        gmail_ids,
                    ),
                )
                .all()
            )
        }

        emails_to_insert = []

        for message in messages:

            gmail_message_id = message["id"]

            if gmail_message_id in existing_ids:
                continue

            message_data = await gmail.get_email(
                gmail_message_id,
            )

            emails_to_insert.append(
                EmailSyncService._build_email_model(
                    user_id=user.id,
                    message_data=message_data,
                )
            )

        if not emails_to_insert:
            return 0

        try:

            db.add_all(
                emails_to_insert,
            )

            db.commit()

        except Exception:

            db.rollback()
            raise

        logger.info(
            "Inserted %s new emails.",
            len(emails_to_insert),
        )

        for email in emails_to_insert:
            db.refresh(email)

        email_ids = [
            email.id
            for email in emails_to_insert
        ]

        for email_id in email_ids:
            process_email.delay(
                email_id,
            )

        logger.info(
            "Queued %s emails for intelligence processing.",
            len(email_ids),
        )

        return len(email_ids)

    @staticmethod
    def _clean_email_body(
        body: str,
    ) -> str:
        """
        Convert HTML emails to plain text and limit body size.
        """

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

        return body[
            : EmailSyncService.MAX_EMAIL_LENGTH
        ]

    @staticmethod
    def _build_email_model(
        user_id: int,
        message_data: dict,
    ) -> Email:
        """
        Convert a Gmail API message into an Email model.
        """

        payload = message_data.get(
            "payload",
            {},
        )

        headers = {
            header["name"]: header["value"]
            for header in payload.get(
                "headers",
                [],
            )
        }

        sender = headers.get(
            "From",
            "",
        )

        recipient = headers.get(
            "To",
            "",
        )

        subject = headers.get(
            "Subject",
            "",
        )

        received_at = None

        try:

            if headers.get(
                "Date",
            ):
                received_at = parsedate_to_datetime(
                    headers["Date"],
                )

        except Exception:
            pass

        body = EmailSyncService._extract_body(
            payload,
        )

        body = EmailSyncService._clean_email_body(
            body,
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
                "",
            ),
            body=body,
            label_ids=message_data.get(
                "labelIds",
                [],
            ),
            received_at=received_at,
            is_processed=False,
        )

    @staticmethod
    def _extract_body(
        payload: dict,
    ) -> str:
        """
        Extract the email body from the Gmail payload.
        """

        body_data = (
            payload.get(
                "body",
                {},
            ).get(
                "data",
            )
        )

        if body_data:

            try:

                return (
                    base64.urlsafe_b64decode(
                        body_data,
                    )
                    .decode(
                        "utf-8",
                        errors="ignore",
                    )
                )

            except Exception:
                return ""

        for part in payload.get(
            "parts",
            [],
        ):

            mime_type = part.get(
                "mimeType",
            )

            if mime_type not in (
                "text/plain",
                "text/html",
            ):
                continue

            data = (
                part.get(
                    "body",
                    {},
                ).get(
                    "data",
                )
            )

            if not data:
                continue

            try:

                return (
                    base64.urlsafe_b64decode(
                        data,
                    )
                    .decode(
                        "utf-8",
                        errors="ignore",
                    )
                )

            except Exception:
                continue

        return ""