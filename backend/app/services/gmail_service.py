from typing import Any

import httpx
import base64
from email.mime.text import MIMEText

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
            "Authorization": (
                f"Bearer {access_token}"
            )
        }

    async def list_emails(
        self,
        query: str | None = None,
        max_results: int = 100,
    ) -> dict[str, Any]:

        params = {
            "maxResults": max_results
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
                (
                    f"{self.BASE_URL}/messages/"
                    f"{message_id}"
                ),
                headers=self.headers,
            )

        response.raise_for_status()

        return response.json()

    async def get_thread(
        self,
        thread_id: str,
    ) -> dict[str, Any]:

        async with httpx.AsyncClient() as client:

            response = await client.get(
                (
                    f"{self.BASE_URL}/threads/"
                    f"{thread_id}"
                ),
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
    
    async def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:

        message = MIMEText(body)

        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        payload = {
            "message": {
                "raw": raw,
            }
        }

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
    
    async def update_draft(
        self,
        draft_id: str,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:

        message = MIMEText(body)

        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        payload = {
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