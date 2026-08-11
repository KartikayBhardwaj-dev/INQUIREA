from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.draft_reply import DraftReply

logger = logging.getLogger(__name__)


class DraftRepository:
    """
    Database Access Layer for DraftReply.

    Responsibilities:
    - Create drafts
    - Create draft versions
    - Enforce ownership
    - Load drafts
    - Find current/latest versions
    - Update Gmail metadata
    - Delete drafts
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================
    # CREATE / VERSION
    # =========================================================

    def create_draft(
        self,
        email_id: int,
        content: str,
        user_id: int,
        tone: str = "professional",
        gmail_draft_id: str | None = None,
    ) -> DraftReply:

        if user_id is None:
            raise ValueError(
                "user_id is required when creating a draft."
            )

        try:
            # -------------------------------------------------
            # Find latest version belonging to THIS user
            # -------------------------------------------------

            latest_draft = (
                self.db.query(DraftReply)
                .filter(
                    DraftReply.email_id == email_id,
                    DraftReply.user_id == user_id,
                )
                .order_by(
                    DraftReply.version.desc()
                )
                .first()
            )

            if latest_draft is None:
                next_version = 1
            else:
                next_version = latest_draft.version + 1

            # -------------------------------------------------
            # Make all previous versions non-current
            # for THIS user and email.
            # -------------------------------------------------

            (
                self.db.query(DraftReply)
                .filter(
                    DraftReply.email_id == email_id,
                    DraftReply.user_id == user_id,
                    DraftReply.is_current.is_(True),
                )
                .update(
                    {"is_current": False},
                    synchronize_session=False,
                )
            )

            # -------------------------------------------------
            # Create new version
            # -------------------------------------------------

            draft = DraftReply(
                email_id=email_id,
                user_id=user_id,
                draft=content,
                version=next_version,
                tone=tone,
                gmail_draft_id=gmail_draft_id,
                is_current=True,
            )

            self.db.add(draft)
            self.db.flush()

            logger.info(
                "Created DraftReply ID %s for Email ID %s "
                "User ID %s Version %s.",
                draft.id,
                email_id,
                user_id,
                next_version,
            )

            return draft

        except SQLAlchemyError:
            logger.exception(
                "Failed to create DraftReply for "
                "Email ID %s User ID %s.",
                email_id,
                user_id,
            )
            raise

    # =========================================================
    # READ
    # =========================================================

    def get_by_id(
        self,
        draft_id: int,
        user_id: int,
    ) -> DraftReply | None:

        if user_id is None:
            raise ValueError(
                "user_id is required when loading a draft."
            )

        return (
            self.db.query(DraftReply)
            .filter(
                DraftReply.id == draft_id,
                DraftReply.user_id == user_id,
            )
            .first()
        )

    def get_by_email_id(
        self,
        email_id: int,
        user_id: int,
    ) -> list[DraftReply]:

        if user_id is None:
            raise ValueError(
                "user_id is required when loading drafts."
            )

        return (
            self.db.query(DraftReply)
            .filter(
                DraftReply.email_id == email_id,
                DraftReply.user_id == user_id,
            )
            .order_by(
                DraftReply.version.desc()
            )
            .all()
        )

    def get_latest_draft_for_email(
        self,
        email_id: int,
        user_id: int,
    ) -> DraftReply | None:

        if user_id is None:
            raise ValueError(
                "user_id is required."
            )

        return (
            self.db.query(DraftReply)
            .filter(
                DraftReply.email_id == email_id,
                DraftReply.user_id == user_id,
                DraftReply.is_current.is_(True),
            )
            .order_by(
                DraftReply.version.desc()
            )
            .first()
        )

    def get_latest_version(
        self,
        email_id: int,
        user_id: int,
    ) -> DraftReply | None:

        if user_id is None:
            raise ValueError(
                "user_id is required."
            )

        return (
            self.db.query(DraftReply)
            .filter(
                DraftReply.email_id == email_id,
                DraftReply.user_id == user_id,
            )
            .order_by(
                DraftReply.version.desc()
            )
            .first()
        )

    def get_by_gmail_draft_id(
        self,
        gmail_draft_id: str,
        user_id: int,
    ) -> DraftReply | None:

        return (
            self.db.query(DraftReply)
            .filter(
                DraftReply.gmail_draft_id == gmail_draft_id,
                DraftReply.user_id == user_id,
            )
            .first()
        )

    # =========================================================
    # UPDATE
    # =========================================================

    def update_draft_content(
        self,
        draft_id: int,
        new_content: str,
        user_id: int,
    ) -> DraftReply | None:

        draft = self.get_by_id(
            draft_id,
            user_id=user_id,
        )

        if draft is None:
            logger.warning(
                "Unauthorized/non-existent DraftReply ID %s "
                "for User ID %s.",
                draft_id,
                user_id,
            )
            return None

        try:
            draft.draft = new_content
            self.db.flush()

            logger.info(
                "Updated DraftReply ID %s for User ID %s.",
                draft_id,
                user_id,
            )

            return draft

        except SQLAlchemyError:
            logger.exception(
                "Failed to update DraftReply ID %s.",
                draft_id,
            )
            raise

    def sync_gmail_draft_id(
        self,
        draft_id: int,
        gmail_draft_id: str,
        user_id: int,
    ) -> DraftReply | None:

        draft = self.get_by_id(
            draft_id,
            user_id=user_id,
        )

        if draft is None:
            logger.warning(
                "Unauthorized/non-existent Gmail sync "
                "for DraftReply ID %s User ID %s.",
                draft_id,
                user_id,
            )
            return None

        try:
            draft.gmail_draft_id = gmail_draft_id
            self.db.flush()

            logger.info(
                "Synced Gmail Draft ID '%s' to "
                "DraftReply ID %s.",
                gmail_draft_id,
                draft_id,
            )

            return draft

        except SQLAlchemyError:
            logger.exception(
                "Failed to sync Gmail Draft ID "
                "for DraftReply ID %s.",
                draft_id,
            )
            raise

    # =========================================================
    # DELETE
    # =========================================================

    def delete_draft(
        self,
        draft_id: int,
        user_id: int,
    ) -> bool:

        draft = self.get_by_id(
            draft_id,
            user_id=user_id,
        )

        if draft is None:
            return False

        try:
            self.db.delete(draft)
            self.db.flush()

            logger.info(
                "Deleted DraftReply ID %s for User ID %s.",
                draft_id,
                user_id,
            )

            return True

        except SQLAlchemyError:
            logger.exception(
                "Failed to delete DraftReply ID %s.",
                draft_id,
            )
            raise