from __future__ import annotations

from typing import Any
from backend.app.services.draft_service import DraftService


class DraftTools:
    """
    Thin wrapper around DraftService.
    """

    def __init__(self, service: DraftService):
        self.service = service

    async def generate_reply(
        self,
        email_id: int,
        tone: str = "professional",
        user_id: int | None = None,
    ) -> Any:
        return await self.service.generate_draft(
            email_id=email_id,
            tone=tone,
            user_id=user_id,
        )

    async def rewrite_reply(
        self,
        draft_id: int,
        tone: str = "professional",
        user_id: int | None = None,
    ) -> Any:
        return await self.service.rewrite_draft(
            draft_id=draft_id,
            tone=tone,
            user_id=user_id,
        )

    async def regenerate_reply(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> Any:
        return await self.service.regenerate_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

    def save_draft(
        self,
        draft_id: int,
        content: str,
        user_id: int | None = None,
    ) -> Any:
        return self.service.save_draft(
            draft_id=draft_id,
            content=content,
            user_id=user_id,
        )

    def load_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> Any:
        return self.service.load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )