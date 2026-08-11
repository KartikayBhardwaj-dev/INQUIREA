from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.app.agents.reply_agent import ReplyAgent
from backend.app.models.approval import Approval
from backend.app.models.draft_reply import DraftReply
from backend.app.models.email import Email
from backend.app.repositories.draft_repository import DraftRepository

logger = logging.getLogger(__name__)


class DraftService:
    """
    Draft management service.

    Responsibilities
    ----------------
    - Generate drafts using ReplyAgent
    - Rewrite drafts
    - Regenerate drafts
    - Persist draft versions
    - Manage approvals
    - Load drafts
    """

    def __init__(self, db: Session):
        self.db = db
        self.reply_agent = ReplyAgent()
        self.repository = DraftRepository(db)

    # ---------------------------------------------------------
    # EMAIL
    # ---------------------------------------------------------

    def _load_email(
        self,
        email_id: int,
        user_id: int | None = None,
    ) -> Email | None:

        query = (
            self.db
            .query(Email)
            .filter(Email.id == email_id)
        )

        if (
            user_id is not None
            and hasattr(Email, "user_id")
        ):
            query = query.filter(
                Email.user_id == user_id
            )

        return query.first()

    # ---------------------------------------------------------
    # DRAFT
    # ---------------------------------------------------------

    def load_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> DraftReply | None:

        return self.repository.get_by_id(
            draft_id=draft_id,
            user_id=user_id,
        )

    # ---------------------------------------------------------
    # GENERATE
    # ---------------------------------------------------------

    async def generate_draft(
        self,
        email_id: int,
        tone: str = "professional",
        user_id: int | None = None,
    ) -> DraftReply:

        email = self._load_email(
            email_id,
            user_id=user_id,
        )

        if email is None:
            raise ValueError(
                f"Email with ID {email_id} not found."
            )

        # -----------------------------------------------------
        # Generate content
        # -----------------------------------------------------

        state = {
            "subject": email.subject,
            "body": email.body or "",
            "summary": "",
            "tone": tone,
        }

        agent_result: dict[str, Any] = (
            await self.reply_agent.execute(state)
        )

        generated_content = (
            agent_result.get("draft_reply", "")
        )

        if not generated_content:
            raise ValueError(
                "Reply agent did not generate draft content."
            )

        # -----------------------------------------------------
        # IMPORTANT:
        # Repository handles versioning.
        #
        # First generation:
        #   version = 1
        #
        # Next generation:
        #   version = latest + 1
        # -----------------------------------------------------

        draft = self.repository.create_draft(
            email_id=email.id,
            content=generated_content,
            user_id=user_id,
            tone=tone,
        )

        # -----------------------------------------------------
        # Create approval for this version
        # -----------------------------------------------------

        approval = Approval(
            draft_reply_id=draft.id,
            status="pending",
        )

        self.db.add(approval)

        self.db.commit()
        self.db.refresh(draft)

        logger.info(
            "Generated draft %s for email %s "
            "with version %s.",
            draft.id,
            email.id,
            draft.version,
        )

        return draft

    # ---------------------------------------------------------
    # REWRITE
    # ---------------------------------------------------------

    async def rewrite_draft(
        self,
        draft_id: int,
        tone: str = "professional",
        user_id: int | None = None,
    ) -> DraftReply:

        draft = self.load_draft(
            draft_id,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft with ID {draft_id} not found."
            )

        # -----------------------------------------------------
        # Generate a new version for the same email.
        # -----------------------------------------------------

        return await self.generate_draft(
            email_id=draft.email_id,
            tone=tone,
            user_id=user_id,
        )

    # ---------------------------------------------------------
    # REGENERATE
    # ---------------------------------------------------------

    async def regenerate_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> DraftReply:

        draft = self.load_draft(
            draft_id,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft with ID {draft_id} not found."
            )

        return await self.generate_draft(
            email_id=draft.email_id,
            tone=draft.tone or "professional",
            user_id=user_id,
        )

    # ---------------------------------------------------------
    # SAVE DRAFT
    # ---------------------------------------------------------

    def save_draft(
        self,
        draft_id: int,
        content: str,
        user_id: int | None = None,
    ) -> DraftReply:

        draft = self.load_draft(
            draft_id,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft with ID {draft_id} not found."
            )

        draft.draft = content

        # -----------------------------------------------------
        # Content modification invalidates approval.
        # -----------------------------------------------------

        approval = (
            self.db
            .query(Approval)
            .filter(
                Approval.draft_reply_id == draft.id
            )
            .first()
        )

        if approval:
            approval.status = "pending"

        self.db.commit()
        self.db.refresh(draft)

        logger.info(
            "Saved draft %s and reset approval to pending.",
            draft.id,
        )

        return draft

    # ---------------------------------------------------------
    # CREATE VERSION FROM EXISTING DRAFT
    # ---------------------------------------------------------

    def version_draft(
        self,
        draft_id: int,
        content: str,
        user_id: int | None = None,
    ) -> DraftReply:

        draft = self.load_draft(
            draft_id,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft with ID {draft_id} not found."
            )

        # -----------------------------------------------------
        # Repository determines latest version and increments it.
        # -----------------------------------------------------

        new_draft = self.repository.create_draft(
            email_id=draft.email_id,
            content=content,
            user_id=user_id,
            tone=draft.tone or "professional",
        )

        # -----------------------------------------------------
        # Every new version starts with pending approval.
        # -----------------------------------------------------

        approval = Approval(
            draft_reply_id=new_draft.id,
            status="pending",
        )

        self.db.add(approval)

        self.db.commit()
        self.db.refresh(new_draft)

        logger.info(
            "Created draft version %s (ID %s) "
            "from draft ID %s.",
            new_draft.version,
            new_draft.id,
            draft.id,
        )

        return new_draft