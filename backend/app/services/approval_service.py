from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.app.models.approval import Approval, ApprovalStatus
from backend.app.models.draft_reply import DraftReply

logger = logging.getLogger(__name__)


class ApprovalService:
    """
    Approval lifecycle service.

    Valid state transitions:

        PENDING
           ├── APPROVE → APPROVED
           └── REJECT  → REJECTED

        APPROVED
           └── EDIT/REWRITE/REGENERATE → PENDING

        REJECTED
           └── EDIT/REWRITE/REGENERATE → PENDING

    Editing a draft is handled by DraftService, which calls
    reset_to_pending() when necessary.
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------
    # LOAD
    # ---------------------------------------------------------

    def load_approval(
        self,
        draft_id: int,
    ) -> Approval | None:

        return (
            self.db
            .query(Approval)
            .filter(
                Approval.draft_reply_id == draft_id
            )
            .first()
        )

    def load_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> DraftReply | None:

        query = (
            self.db
            .query(DraftReply)
            .filter(
                DraftReply.id == draft_id
            )
        )

        if user_id is not None:
            query = query.filter(
                DraftReply.user_id == user_id
            )

        return query.first()

    # ---------------------------------------------------------
    # APPROVE
    # ---------------------------------------------------------

    def approve_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> Approval:

        draft = self.load_draft(
            draft_id,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft with ID {draft_id} not found."
            )

        approval = self.load_approval(draft_id)

        # A draft without an approval record is treated
        # as pending.
        if approval is None:
            approval = Approval(
                draft_reply_id=draft_id,
                status=ApprovalStatus.PENDING.value,
            )

            self.db.add(approval)
            self.db.flush()

        self._validate_transition(
            current_status=approval.status,
            new_status=ApprovalStatus.APPROVED.value,
        )

        approval.status = ApprovalStatus.APPROVED.value

        self.db.commit()
        self.db.refresh(approval)

        logger.info(
            "Draft %s approved.",
            draft_id,
        )

        return approval

    # ---------------------------------------------------------
    # REJECT
    # ---------------------------------------------------------

    def reject_draft(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> Approval:

        draft = self.load_draft(
            draft_id,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft with ID {draft_id} not found."
            )

        approval = self.load_approval(draft_id)

        if approval is None:
            approval = Approval(
                draft_reply_id=draft_id,
                status=ApprovalStatus.PENDING.value,
            )

            self.db.add(approval)
            self.db.flush()

        self._validate_transition(
            current_status=approval.status,
            new_status=ApprovalStatus.REJECTED.value,
        )

        approval.status = ApprovalStatus.REJECTED.value

        self.db.commit()
        self.db.refresh(approval)

        logger.info(
            "Draft %s rejected.",
            draft_id,
        )

        return approval

    # ---------------------------------------------------------
    # GET STATUS
    # ---------------------------------------------------------

    def get_status(
        self,
        draft_id: int,
        user_id: int | None = None,
    ) -> str:

        draft = self.load_draft(
            draft_id,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft with ID {draft_id} not found."
            )

        approval = self.load_approval(draft_id)

        if approval is None:
            return ApprovalStatus.PENDING.value

        return approval.status

    # ---------------------------------------------------------
    # VALIDATE STATE TRANSITION
    # ---------------------------------------------------------

    def _validate_transition(
        self,
        current_status: str,
        new_status: str,
    ) -> None:

        valid_statuses = {
            ApprovalStatus.PENDING.value,
            ApprovalStatus.APPROVED.value,
            ApprovalStatus.REJECTED.value,
        }

        if current_status not in valid_statuses:
            raise ValueError(
                f"Invalid current approval status: "
                f"'{current_status}'."
            )

        # -----------------------------------------------------
        # Same state
        # -----------------------------------------------------

        if current_status == new_status:

            if new_status == ApprovalStatus.APPROVED.value:
                raise ValueError(
                    "Draft is already approved."
                )

            if new_status == ApprovalStatus.REJECTED.value:
                raise ValueError(
                    "Draft is already rejected."
                )

            raise ValueError(
                f"Draft is already {current_status}."
            )

        # -----------------------------------------------------
        # PENDING → APPROVED
        # PENDING → REJECTED
        # -----------------------------------------------------

        if current_status == ApprovalStatus.PENDING.value:

            if new_status in {
                ApprovalStatus.APPROVED.value,
                ApprovalStatus.REJECTED.value,
            }:
                return

        # -----------------------------------------------------
        # APPROVED cannot directly become REJECTED.
        # It must first be edited/re-written, which creates
        # a pending draft/version.
        # -----------------------------------------------------

        if current_status == ApprovalStatus.APPROVED.value:

            raise ValueError(
                f"Cannot transition draft from "
                f"'{current_status}' to '{new_status}'. "
                f"Edit or rewrite the draft first."
            )

        # -----------------------------------------------------
        # REJECTED cannot directly become APPROVED.
        # It must first be edited/re-written.
        # -----------------------------------------------------

        if current_status == ApprovalStatus.REJECTED.value:

            raise ValueError(
                f"Cannot transition draft from "
                f"'{current_status}' to '{new_status}'. "
                f"Edit or rewrite the draft first."
            )

        raise ValueError(
            f"Invalid approval transition: "
            f"{current_status} → {new_status}."
        )

    # ---------------------------------------------------------
    # RESET TO PENDING
    # ---------------------------------------------------------

    def reset_to_pending(
        self,
        draft_id: int,
        user_id: int | None = None,
        commit: bool = True,
    ) -> Approval:

        draft = self.load_draft(
            draft_id,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft with ID {draft_id} not found."
            )

        approval = self.load_approval(draft_id)

        # -----------------------------------------------------
        # Create approval if it doesn't exist.
        # -----------------------------------------------------

        if approval is None:

            approval = Approval(
                draft_reply_id=draft_id,
                status=ApprovalStatus.PENDING.value,
            )

            self.db.add(approval)

        else:

            # Editing a draft is allowed to reset:
            #
            # APPROVED → PENDING
            # REJECTED → PENDING
            #
            # It is also harmless for PENDING → PENDING.
            approval.status = ApprovalStatus.PENDING.value

        if commit:
            self.db.commit()
            self.db.refresh(approval)
        else:
            self.db.flush()

        logger.info(
            "Draft %s reset to pending.",
            draft_id,
        )

        return approval