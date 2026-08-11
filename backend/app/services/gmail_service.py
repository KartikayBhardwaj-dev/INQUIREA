from __future__ import annotations

from typing import Any
import base64
from email.mime.text import MIMEText

import httpx


class GmailService:

    BASE_URL = (
        "https://gmail.googleapis.com/"
        "gmail/v1/users/me"
    )

    def __init__(
        self,
        access_token: str,
    ):
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    # =========================================================
    # EMAILS
    # =========================================================

    async def list_emails(
        self,
        query: str | None = None,
        max_results: int = 100,
    ) -> dict[str, Any]:

        params = {
            "maxResults": max_results,
        }

        if query:
            params["q"] = query

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/messages",
                headers=self.headers,
                params=params,
            )

        response.raise_for_status()

        return response.json()

    async def get_email(
        self,
        message_id: str,
    ) -> dict[str, Any]:

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/messages/{message_id}",
                headers=self.headers,
                params={
                    "format": "full",
                },
            )

        response.raise_for_status()

        return response.json()

    async def get_thread(
        self,
        thread_id: str,
    ) -> dict[str, Any]:

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/threads/{thread_id}",
                headers=self.headers,
            )

        response.raise_for_status()

        return response.json()

    async def get_attachment(
        self,
        message_id: str,
        attachment_id: str,
    ) -> dict[str, Any]:

        async with httpx.AsyncClient() as client:
            response = await client.get(
                (
                    f"{self.BASE_URL}/messages/"
                    f"{message_id}/attachments/"
                    f"{attachment_id}"
                ),
                headers=self.headers,
            )

        response.raise_for_status()

        return response.json()

    # =========================================================
    # SUBJECT HELPER
    # =========================================================

    @staticmethod
    def _reply_subject(subject: str) -> str:
        """
        Ensure the subject is formatted as a reply.

        Examples:

            Meeting
                -> Re: Meeting

            Re: Meeting
                -> Re: Meeting

            re: Meeting
                -> Re: Meeting
        """

        subject = (subject or "").strip()

        if not subject:
            return "Re:"

        if subject.lower().startswith("re:"):
            return subject

        return f"Re: {subject}"

    # =========================================================
    # CREATE GMAIL REPLY DRAFT
    # =========================================================

    async def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
        message_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a Gmail draft.

        For replies:

            To:
                original sender

            Subject:
                Re: original subject

            Thread:
                original Gmail thread ID

            In-Reply-To:
                original Gmail message ID, when available

            References:
                original Gmail message ID, when available

        This allows Gmail to keep the draft inside the
        correct conversation/thread.
        """

        message = MIMEText(
            body,
            "plain",
            "utf-8",
        )

        message["To"] = to
        message["Subject"] = self._reply_subject(subject)

        # -----------------------------------------------------
        # Reply headers
        # -----------------------------------------------------

        if message_id:
            # Gmail message IDs are normally API IDs, not RFC
            # Message-ID values. Therefore, only use this field
            # if the value stored in your Email model represents
            # the actual RFC Message-ID header.
            message["In-Reply-To"] = message_id
            message["References"] = message_id

        raw = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        payload: dict[str, Any] = {
            "message": {
                "raw": raw,
            }
        }

        # -----------------------------------------------------
        # Gmail thread association
        # -----------------------------------------------------

        if thread_id:
            payload["message"]["threadId"] = thread_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/drafts",
                headers=self.headers,
                json=payload,
            )

        response.raise_for_status()

        return response.json()

    # =========================================================
    # UPDATE GMAIL REPLY DRAFT
    # =========================================================

    async def update_draft(
        self,
        draft_id: str,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
        message_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Update an existing Gmail reply draft.

        The same reply/thread metadata is preserved when
        updating the Gmail draft.
        """

        message = MIMEText(
            body,
            "plain",
            "utf-8",
        )

        message["To"] = to
        message["Subject"] = self._reply_subject(subject)

        if message_id:
            message["In-Reply-To"] = message_id
            message["References"] = message_id

        raw = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        payload: dict[str, Any] = {
            "id": draft_id,
            "message": {
                "raw": raw,
            },
        }

        if thread_id:
            payload["message"]["threadId"] = thread_id

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.BASE_URL}/drafts/{draft_id}",
                headers=self.headers,
                json=payload,
            )

        response.raise_for_status()

        return response.json()

    # =========================================================
    # SEND GMAIL DRAFT
    # =========================================================

    async def send_draft(
        self,
        draft_id: str,
    ) -> dict[str, Any]:

        payload = {
            "id": draft_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/drafts/send",
                headers=self.headers,
                json=payload,
            )

        response.raise_for_status()

        return response.json()

    # =========================================================
    # BODY DECODING
    # =========================================================

    @staticmethod
    def _decode_body(
        data: str | None,
    ) -> str:

        if not data:
            return ""

        try:
            decoded = base64.urlsafe_b64decode(
                data
                + "=" * (
                    -len(data) % 4
                )
            )

            return decoded.decode(
                "utf-8",
                errors="replace",
            )

        except Exception:
            return ""

    @classmethod
    def _extract_body(
        cls,
        payload: dict[str, Any] | None,
    ) -> str:

        if not payload:
            return ""

        body = payload.get(
            "body"
        ) or {}

        data = body.get(
            "data"
        )

        if data:
            return cls._decode_body(
                data
            )

        parts = payload.get(
            "parts"
        ) or []

        plain_text = ""
        html_text = ""

        for part in parts:

            mime_type = part.get(
                "mimeType",
                "",
            )

            part_body = (
                part.get("body")
                or {}
            )

            part_data = part_body.get(
                "data"
            )

            if part_data:

                decoded = cls._decode_body(
                    part_data
                )

                if mime_type == "text/plain":
                    plain_text += decoded

                elif mime_type == "text/html":
                    html_text += decoded

            nested_parts = part.get(
                "parts"
            )

            if nested_parts:

                nested_body = cls._extract_body(
                    {
                        "parts": nested_parts
                    }
                )

                if nested_body:
                    plain_text += nested_body

        if plain_text.strip():
            return plain_text.strip()

        if html_text.strip():
            return html_text.strip()

        return ""