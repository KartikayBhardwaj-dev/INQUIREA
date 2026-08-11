from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.app.agents.reply_agent import ReplyAgent
from backend.app.models.approval import Approval, ApprovalStatus
from backend.app.models.draft_reply import DraftReply
from backend.app.models.email import Email
from backend.app.repositories.draft_repository import DraftRepository
from backend.app.services.approval_service import ApprovalService

logger = logging.getLogger(__name__)


class DraftService:
    """
    Draft management service.

    Responsibilities
    ----------------
    - Generate drafts
    - Rewrite drafts
    - Regenerate drafts
    - Persist draft versions
    - Manage approval lifecycle
    - Load drafts

    Approval lifecycle:

        New draft
            ↓
        PENDING
            ↓
        APPROVED / REJECTED

        Any edit/rewrite/regeneration
            ↓
        New version
            ↓
        PENDING
    """

    def __init__(self, db: Session):
        self.db = db
        self.reply_agent = ReplyAgent()
        self.repository = DraftRepository(db)
        self.approval_service = ApprovalService(db)

    # =========================================================
    # EMAIL
    # =========================================================

    def _load_email(
        self,
        email_id: int,
        user_id: int | None = None,
    ) -> Email | None:

        query = (
            self.db
            .query(Email)
            .filter(
                Email.id == email_id
            )
        )

        if user_id is not None:
            query = query.filter(
                Email.user_id == user_id
            )

        return query.first()

    # =========================================================
    # DRAFT
    # =========================================================

    def load_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> DraftReply | None:

        return self.repository.get_by_id(
            draft_id=draft_id,
            user_id=user_id,
        )

    # =========================================================
    # GENERATE DRAFT
    # =========================================================

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
        # Repository handles:
        #
        # - latest version lookup
        # - version + 1
        # - old is_current = False
        # - new is_current = True
        # -----------------------------------------------------

        draft = self.repository.create_draft(
            email_id=email.id,
            content=generated_content,
            user_id=user_id,
            tone=tone,
        )

        # -----------------------------------------------------
        # Every newly generated version starts PENDING.
        # -----------------------------------------------------

        approval = self.approval_service.reset_to_pending(
            draft_id=draft.id,
            user_id=user_id,
            commit=False,
        )

        # -----------------------------------------------------
        # Commit draft + approval together.
        # -----------------------------------------------------

        self.db.commit()
        self.db.refresh(draft)
        self.db.refresh(approval)

        logger.info(
            "Generated draft %s for email %s. "
            "Version=%s, approval=%s.",
            draft.id,
            email.id,
            draft.version,
            approval.status,
        )

        return draft

    # =========================================================
    # REWRITE DRAFT
    # =========================================================

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
        # IMPORTANT:
        #
        # Rewrite creates a NEW VERSION.
        #
        # Old:
        #   version N
        #   is_current = False
        #   approval remains historical
        #
        # New:
        #   version N+1
        #   is_current = True
        #   approval = PENDING
        # -----------------------------------------------------

        new_draft = await self.generate_draft(
            email_id=draft.email_id,
            tone=tone,
            user_id=user_id,
        )

        logger.info(
            "Rewrote draft %s → new draft %s. "
            "New version=%s, approval=pending.",
            draft.id,
            new_draft.id,
            new_draft.version,
        )

        return new_draft

    # =========================================================
    # REGENERATE DRAFT
    # =========================================================

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

        # -----------------------------------------------------
        # Regeneration also creates a new version.
        # -----------------------------------------------------

        new_draft = await self.generate_draft(
            email_id=draft.email_id,
            tone=draft.tone or "professional",
            user_id=user_id,
        )

        logger.info(
            "Regenerated draft %s → new draft %s. "
            "New version=%s, approval=pending.",
            draft.id,
            new_draft.id,
            new_draft.version,
        )

        return new_draft

    # =========================================================
    # SAVE / EDIT EXISTING DRAFT
    # =========================================================

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

        if not content or not content.strip():
            raise ValueError(
                "Draft content cannot be empty."
            )

        # -----------------------------------------------------
        # Edit existing draft content.
        # -----------------------------------------------------

        draft.draft = content.strip()

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # Editing invalidates any previous approval.
        #
        # APPROVED → PENDING
        # REJECTED → PENDING
        # PENDING  → PENDING
        # -----------------------------------------------------

        self.approval_service.reset_to_pending(
            draft_id=draft.id,
            user_id=user_id,
            commit=False,
        )

        self.db.commit()
        self.db.refresh(draft)

        logger.info(
            "Edited draft %s. Approval reset to pending.",
            draft.id,
        )

        return draft

    # =========================================================
    # CREATE VERSION FROM EXISTING DRAFT
    # =========================================================

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

        if not content or not content.strip():
            raise ValueError(
                "Draft content cannot be empty."
            )

        # -----------------------------------------------------
        # Repository:
        #
        # latest version + 1
        # old current = False
        # new current = True
        # -----------------------------------------------------

        new_draft = self.repository.create_draft(
            email_id=draft.email_id,
            content=content.strip(),
            user_id=user_id,
            tone=draft.tone or "professional",
        )

        # -----------------------------------------------------
        # New version ALWAYS starts pending.
        # -----------------------------------------------------

        approval = self.approval_service.reset_to_pending(
            draft_id=new_draft.id,
            user_id=user_id,
            commit=False,
        )

        self.db.commit()

        self.db.refresh(new_draft)
        self.db.refresh(approval)

        logger.info(
            "Created draft version %s (ID %s) "
            "from draft ID %s. Approval=%s.",
            new_draft.version,
            new_draft.id,
            draft.id,
            approval.status,
        )

        return new_draft