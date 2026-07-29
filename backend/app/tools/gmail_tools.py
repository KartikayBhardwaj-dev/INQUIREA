from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from backend.app.services.gmail_action_service import GmailActionService


class GmailTools:
    """
    Thin wrapper around GmailActionService.
    """

    def __init__(self, db: Session):
        self.service = GmailActionService(db)

    async def send_reply(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        return await self.service.send_reply(
            draft_id=draft_id,
            user_id=user_id,
        )

    async def save_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        return await self.service.save_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

    async def update_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        return await self.service.update_draft(
            draft_id=draft_id,
            user_id=user_id,
        )