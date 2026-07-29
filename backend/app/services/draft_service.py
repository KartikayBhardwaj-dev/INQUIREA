from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.app.agents.reply_agent import ReplyAgent
from backend.app.models.approval import Approval
from backend.app.models.draft_reply import DraftReply
from backend.app.models.email import Email

logger = logging.getLogger(__name__)


class DraftService:
    """
    Draft management service.

    Responsibilities
    ----------------
    - Generate drafts using ReplyAgent
    - Rewrite drafts
    - Regenerate drafts
    - Persist drafts
    - Version drafts
    - Load drafts
    """

    def __init__(self, db: Session):
        self.db = db
        self.reply_agent = ReplyAgent()

    def _load_email(self, email_id: int, user_id: int | None = None) -> Email | None:
        query = self.db.query(Email).filter(Email.id == email_id)
        if user_id is not None and hasattr(Email, "user_id"):
            query = query.filter(Email.user_id == user_id)
        return query.first()

    def load_draft(self, draft_id: int, user_id: int | None = None) -> DraftReply | None:
        query = self.db.query(DraftReply).filter(DraftReply.id == draft_id)
        if user_id is not None and hasattr(DraftReply, "user_id"):
            query = query.filter(DraftReply.user_id == user_id)
        return query.first()

    async def generate_draft(
        self,
        email_id: int,
        tone: str = "professional",
        user_id: int | None = None,
    ) -> DraftReply:
        email = self._load_email(email_id, user_id=user_id)
        if email is None:
            raise ValueError(f"Email with ID {email_id} not found.")

        # Deactivate previous active drafts for this email
        self.db.query(DraftReply).filter(
            DraftReply.email_id == email.id,
            DraftReply.is_current == True, # noqa: E712
        ).update({"is_current": False}, synchronize_session=False)

        state = {
            "subject": email.subject,
            "body": email.body or "",
            "summary": "",
            "tone": tone,
        }

        agent_result: dict[str, Any] = await self.reply_agent.execute(state)
        generated_content = agent_result.get("draft_reply", "")

        draft = DraftReply(
            email_id=email.id,
            draft=generated_content,
            version=1,
            tone=tone,
            is_current=True,
        )
        if user_id is not None and hasattr(DraftReply, "user_id"):
            setattr(draft, "user_id", user_id)

        self.db.add(draft)
        self.db.flush()

        approval = Approval(
            draft_reply_id=draft.id,
            status="pending",
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(draft)

        logger.info("Generated draft %s for email %s", draft.id, email.id)
        return draft

    async def rewrite_draft(
        self,
        draft_id: int,
        tone: str = "professional",
        user_id: int | None = None,
    ) -> DraftReply:
        draft = self.load_draft(draft_id, user_id=user_id)
        if draft is None:
            raise ValueError(f"Draft with ID {draft_id} not found.")

        return await self.generate_draft(
            email_id=draft.email_id,
            tone=tone,
            user_id=user_id,
        )

    async def regenerate_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> DraftReply:
        draft = self.load_draft(draft_id, user_id=user_id)
        if draft is None:
            raise ValueError(f"Draft with ID {draft_id} not found.")

        return await self.generate_draft(
            email_id=draft.email_id,
            tone=draft.tone or "professional",
            user_id=user_id,
        )

    def save_draft(
        self,
        draft_id: int,
        content: str,
        user_id: int | None = None,
    ) -> DraftReply:
        draft = self.load_draft(draft_id, user_id=user_id)
        if draft is None:
            raise ValueError(f"Draft with ID {draft_id} not found.")

        draft.draft = content

        # Reset approval status to pending upon content edits
        approval = (
            self.db.query(Approval)
            .filter(Approval.draft_reply_id == draft.id)
            .first()
        )
        if approval:
            approval.status = "pending"

        self.db.commit()
        self.db.refresh(draft)

        logger.info("Saved draft %s and reset approval to pending.", draft.id)
        return draft

    def version_draft(
        self,
        draft_id: int,
        content: str,
        user_id: int | None = None,
    ) -> DraftReply:
        draft = self.load_draft(draft_id, user_id=user_id)
        if draft is None:
            raise ValueError(f"Draft with ID {draft_id} not found.")

        # Mark former draft version as not current
        draft.is_current = False

        new_version_num = getattr(draft, "version", 1) + 1

        new_draft = DraftReply(
            email_id=draft.email_id,
            draft=content,
            version=new_version_num,
            tone=draft.tone,
            is_current=True,
        )
        if user_id is not None and hasattr(DraftReply, "user_id"):
            setattr(new_draft, "user_id", user_id)

        self.db.add(new_draft)
        self.db.flush()

        approval = Approval(
            draft_reply_id=new_draft.id,
            status="pending",
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(new_draft)

        logger.info("Created draft version %s from draft %s", new_draft.id, draft.id)
        return new_draft