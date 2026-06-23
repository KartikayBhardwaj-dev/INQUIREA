from typing import Any

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