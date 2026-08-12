from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.app.agents.reply_agent import ReplyAgent
from backend.app.models.approval import Approval
from backend.app.models.draft_reply import DraftReply
from backend.app.models.email import Email
from backend.app.repositories.draft_repository import DraftRepository
from backend.app.services.approval_service import ApprovalService

logger = logging.getLogger(__name__)


class DraftService:
    """
    Draft management service.

    Responsibilities:
    - Generate drafts
    - Rewrite drafts
    - Regenerate drafts
    - Persist draft versions
    - Manage approval lifecycle
    - Enforce user ownership
    """

    def __init__(self, db: Session):
        self.db = db
        self.reply_agent = ReplyAgent()
        self.repository = DraftRepository(db)
        self.approval_service = ApprovalService(db)

    # =========================================================
    # OWNERSHIP
    # =========================================================

    def _require_user(self, user_id: int | None) -> int:
        if user_id is None:
            raise ValueError(
                "Authenticated user_id is required."
            )

        return user_id

    # =========================================================
    # EMAIL
    # =========================================================

    def _load_email(
        self,
        email_id: int,
        user_id: int,
    ) -> Email | None:

        user_id = self._require_user(user_id)

        return (
            self.db.query(Email)
            .filter(
                Email.id == email_id,
                Email.user_id == user_id,
            )
            .first()
        )

    # =========================================================
    # DRAFT
    # =========================================================

    def load_draft(
        self,
        draft_id: int,
        user_id: int,
    ) -> DraftReply | None:

        user_id = self._require_user(user_id)

        return self.repository.get_by_id(
            draft_id=draft_id,
            user_id=user_id,
        )

    # =========================================================
    # GENERATE
    # =========================================================

    async def generate_draft(
        self,
        email_id: int,
        tone: str = "professional",
        user_id: int | None = None,
    ) -> DraftReply:

        user_id = self._require_user(user_id)

        # -----------------------------------------------------
        # IMPORTANT:
        # Email MUST belong to authenticated user.
        # -----------------------------------------------------

        email = self._load_email(
            email_id=email_id,
            user_id=user_id,
        )

        if email is None:
            raise ValueError(
                f"Email with ID {email_id} not found "
                f"for user {user_id}."
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
        # version 1
        # version N + 1
        # old current = False
        # new current = True
        #
        # AND stores user_id.
        # -----------------------------------------------------

        draft = self.repository.create_draft(
            email_id=email.id,
            content=generated_content,
            user_id=user_id,
            tone=tone,
        )

        # -----------------------------------------------------
        # Every new version gets PENDING approval.
        # -----------------------------------------------------

        approval = self.approval_service.reset_to_pending(
            draft_id=draft.id,
            user_id=user_id,
            commit=False,
        )

        self.db.commit()

        self.db.refresh(draft)
        self.db.refresh(approval)

        logger.info(
            "Generated draft ID %s for Email ID %s "
            "User ID %s Version %s Approval %s.",
            draft.id,
            email.id,
            user_id,
            draft.version,
            approval.status,
        )

        return draft

    # =========================================================
    # REWRITE
    # =========================================================

    async def rewrite_draft(
    self,
    draft_id: int,
    tone: str = "professional",
    instruction: str | None = None,
    user_id: int | None = None,
) -> DraftReply:

        user_id = self._require_user(user_id)

    # ---------------------------------------------------------
    # Load existing draft and verify ownership.
    # ---------------------------------------------------------

        draft = self.load_draft(
        draft_id=draft_id,
        user_id=user_id,
    )

        if draft is None:
            raise ValueError(
            f"Draft with ID {draft_id} not found."
        )

        if instruction is None or not instruction.strip():
            raise ValueError(
            "Rewrite instruction is required."
        )

    # ---------------------------------------------------------
    # Verify associated email belongs to the same user.
    # ---------------------------------------------------------

        email = self._load_email(
        email_id=draft.email_id,
        user_id=user_id,
    )

        if email is None:
            raise ValueError(
            f"Email with ID {draft.email_id} not found "
            f"for user {user_id}."
        )

    # ---------------------------------------------------------
    # Ask the reply agent to rewrite the CURRENT draft.
    #
    # Important:
    # We pass the existing draft content rather than
    # generating a completely unrelated reply from the email.
    # ---------------------------------------------------------

        state = {
        "subject": email.subject,
        "body": email.body or "",
        "summary": "",
        "tone": tone,
        "draft_reply": draft.draft,
        "instruction": instruction.strip(),
    }

        agent_result: dict[str, Any] = (
        await self.reply_agent.execute(state)
    )

        rewritten_content = (
        agent_result.get("draft_reply", "")
    )

        if not rewritten_content:
            raise ValueError(
            "Reply agent did not generate rewritten content."
        )

    # ---------------------------------------------------------
    # IMPORTANT:
    #
    # Do NOT overwrite the existing draft.
    #
    # Create a completely new DraftReply version.
    # Repository should:
    #
    #   old draft -> is_current=False
    #   new draft -> version=N+1
    #   new draft -> is_current=True
    # ---------------------------------------------------------

        new_draft = self.repository.create_draft(
        email_id=draft.email_id,
        content=rewritten_content,
        user_id=user_id,
        tone=tone,
    )

    # ---------------------------------------------------------
    # Every rewritten version requires fresh approval.
    # ---------------------------------------------------------

        approval = self.approval_service.reset_to_pending(
        draft_id=new_draft.id,
        user_id=user_id,
        commit=False,
    )

        self.db.commit()

        self.db.refresh(new_draft)
        self.db.refresh(approval)

        logger.info(
        "Rewrote Draft ID %s into new Draft ID %s "
        "Version %s for User ID %s. "
        "Instruction=%s Approval=%s.",
        draft.id,
        new_draft.id,
        new_draft.version,
        user_id,
        instruction,
        approval.status,
    )

        return new_draft

    # =========================================================
    # REGENERATE
    # =========================================================

    async def regenerate_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> DraftReply:

        user_id = self._require_user(user_id)

        draft = self.load_draft(
            draft_id=draft_id,
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

    # =========================================================
    # SAVE / EDIT
    # =========================================================

    def save_draft(
        self,
        draft_id: int,
        content: str,
        user_id: int | None = None,
    ) -> DraftReply:

        user_id = self._require_user(user_id)

        draft = self.load_draft(
            draft_id=draft_id,
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

        draft.draft = content.strip()

        # Editing invalidates approval.
        self.approval_service.reset_to_pending(
            draft_id=draft.id,
            user_id=user_id,
            commit=False,
        )

        self.db.commit()
        self.db.refresh(draft)

        logger.info(
            "Edited Draft ID %s for User ID %s. "
            "Approval reset to pending.",
            draft_id,
            user_id,
        )

        return draft

    # =========================================================
    # CREATE VERSION
    # =========================================================

    def version_draft(
        self,
        draft_id: int,
        content: str,
        user_id: int | None = None,
    ) -> DraftReply:

        user_id = self._require_user(user_id)

        draft = self.load_draft(
            draft_id=draft_id,
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
        # Repository creates:
        #
        # latest version + 1
        # previous current = False
        # new current = True
        # correct user_id
        # -----------------------------------------------------

        new_draft = self.repository.create_draft(
            email_id=draft.email_id,
            content=content.strip(),
            user_id=user_id,
            tone=draft.tone or "professional",
        )

        # New version starts pending.
        approval = self.approval_service.reset_to_pending(
            draft_id=new_draft.id,
            user_id=user_id,
            commit=False,
        )

        self.db.commit()

        self.db.refresh(new_draft)
        self.db.refresh(approval)

        logger.info(
            "Created version %s Draft ID %s "
            "from Draft ID %s for User ID %s. "
            "Approval=%s.",
            new_draft.version,
            new_draft.id,
            draft.id,
            user_id,
            approval.status,
        )

        return new_draft