from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.app.models.approval import Approval
from backend.app.models.approval import ApprovalStatus
from backend.app.models.draft_reply import DraftReply

logger = logging.getLogger(__name__)


class ApprovalService:
    """
    Approval lifecycle:

        PENDING
          ├── APPROVE → APPROVED
          └── REJECT  → REJECTED

        APPROVED
          └── EDIT / REWRITE → PENDING

        REJECTED
          └── EDIT / REWRITE → PENDING

    Transaction rule:

        Service operation
            ↓
        DB changes
            ↓
        flush()
            ↓
        commit()

        Exception
            ↓
        rollback()
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================
    # LOAD
    # =========================================================

    def load_approval(
        self,
        draft_id: int,
    ) -> Approval | None:

        return (
            self.db.query(Approval)
            .filter(
                Approval.draft_reply_id == draft_id
            )
            .first()
        )

    def load_draft(
        self,
        draft_id: int,
        user_id: int,
    ) -> DraftReply | None:

        if user_id is None:
            raise ValueError(
                "Authenticated user_id is required."
            )

        return (
            self.db.query(DraftReply)
            .filter(
                DraftReply.id == draft_id,
                DraftReply.user_id == user_id,
            )
            .first()
        )

    # =========================================================
    # APPROVE
    # =========================================================

    def approve_draft(
        self,
        draft_id: int,
        user_id: int,
    ) -> Approval:

        try:
            draft = self.load_draft(
                draft_id=draft_id,
                user_id=user_id,
            )

            if draft is None:
                raise ValueError(
                    f"Draft {draft_id} not found."
                )

            approval = self.load_approval(
                draft_id=draft_id,
            )

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

            # Make sure SQLAlchemy sends the UPDATE.
            self.db.flush()

            # Standalone service workflow:
            # commit only after everything succeeded.
            self.db.commit()

            self.db.refresh(approval)

            logger.info(
                "Draft %s approved by User %s.",
                draft_id,
                user_id,
            )

            return approval

        except Exception:
            self.db.rollback()
            raise

    # =========================================================
    # REJECT
    # =========================================================

    def reject_draft(
        self,
        draft_id: int,
        user_id: int,
    ) -> Approval:

        try:
            draft = self.load_draft(
                draft_id=draft_id,
                user_id=user_id,
            )

            if draft is None:
                raise ValueError(
                    f"Draft {draft_id} not found."
                )

            approval = self.load_approval(
                draft_id=draft_id,
            )

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

            self.db.flush()

            self.db.commit()

            self.db.refresh(approval)

            logger.info(
                "Draft %s rejected by User %s.",
                draft_id,
                user_id,
            )

            return approval

        except Exception:
            self.db.rollback()
            raise

    # =========================================================
    # STATUS
    # =========================================================

    def get_status(
        self,
        draft_id: int,
        user_id: int,
    ) -> str:

        draft = self.load_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        if draft is None:
            raise ValueError(
                f"Draft {draft_id} not found."
            )

        approval = self.load_approval(
            draft_id=draft_id,
        )

        if approval is None:
            return ApprovalStatus.PENDING.value

        return approval.status

    # =========================================================
    # TRANSITION VALIDATION
    # =========================================================

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

        if new_status not in valid_statuses:
            raise ValueError(
                f"Invalid target approval status: "
                f"'{new_status}'."
            )

        if (
            current_status == ApprovalStatus.PENDING.value
            and new_status == ApprovalStatus.APPROVED.value
        ):
            return

        if (
            current_status == ApprovalStatus.PENDING.value
            and new_status == ApprovalStatus.REJECTED.value
        ):
            return

        raise ValueError(
            f"Invalid approval transition: "
            f"{current_status} → {new_status}."
        )

    # =========================================================
    # RESET TO PENDING
    # =========================================================

    def reset_to_pending(
        self,
        draft_id: int,
        user_id: int,
        commit: bool = True,
    ) -> Approval:

        try:
            draft = self.load_draft(
                draft_id=draft_id,
                user_id=user_id,
            )

            if draft is None:
                raise ValueError(
                    f"Draft {draft_id} not found."
                )

            approval = self.load_approval(
                draft_id=draft_id,
            )

            if approval is None:
                approval = Approval(
                    draft_reply_id=draft_id,
                    status=ApprovalStatus.PENDING.value,
                )

                self.db.add(approval)

            else:
                approval.status = (
                    ApprovalStatus.PENDING.value
                )

            # Always flush so the caller can use the
            # generated/updated DB state.
            self.db.flush()

            if commit:
                self.db.commit()
                self.db.refresh(approval)

            logger.info(
                "Draft %s reset to PENDING for User %s.",
                draft_id,
                user_id,
            )

            return approval

        except Exception:
            # If this method participates in a larger
            # transaction, the caller passes commit=False.
            #
            # In that case the caller still owns the transaction,
            # so rollback is intentionally left to the caller.
            if commit:
                self.db.rollback()

            raise