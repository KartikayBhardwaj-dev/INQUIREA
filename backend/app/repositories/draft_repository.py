from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.draft_reply import DraftReply

logger = logging.getLogger(__name__)


class DraftRepository:
    """
    Database Access Layer for DraftReply entity.

    Responsibilities:
    - Create draft versions
    - Load drafts
    - Find current/latest drafts
    - Update draft metadata
    - Delete drafts
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------
    # CREATE / VERSION
    # ---------------------------------------------------------

    def create_draft(
        self,
        email_id: int,
        content: str,
        user_id: Optional[int] = None,
        tone: str = "professional",
        gmail_draft_id: Optional[str] = None,
    ) -> DraftReply:
        """
        Create a new draft version.

        Versioning rules:

        No previous draft:
            version = 1
            is_current = True

        Existing versions:
            new_version = latest.version + 1
            all previous versions = is_current False
            new version = is_current True
        """

        try:
            # -------------------------------------------------
            # Find the latest existing version
            # -------------------------------------------------

            latest_query = (
                self.db.query(DraftReply)
                .filter(
                    DraftReply.email_id == email_id,
                )
            )

            if user_id is not None:
                latest_query = latest_query.filter(
                    DraftReply.user_id == user_id
                )

            latest_draft = (
                latest_query
                .order_by(DraftReply.version.desc())
                .first()
            )

            # -------------------------------------------------
            # Calculate next version
            # -------------------------------------------------

            if latest_draft is None:
                next_version = 1
            else:
                next_version = latest_draft.version + 1

            # -------------------------------------------------
            # Deactivate all previous current versions
            # -------------------------------------------------

            current_query = (
                self.db.query(DraftReply)
                .filter(
                    DraftReply.email_id == email_id,
                    DraftReply.is_current.is_(True),
                )
            )

            if user_id is not None:
                current_query = current_query.filter(
                    DraftReply.user_id == user_id
                )

            current_query.update(
                {"is_current": False},
                synchronize_session=False,
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
                "with version %s.",
                draft.id,
                email_id,
                next_version,
            )

            return draft

        except SQLAlchemyError:
            logger.exception(
                "Failed to create DraftReply for Email ID %s",
                email_id,
            )
            raise

    # ---------------------------------------------------------
    # READ
    # ---------------------------------------------------------

    def get_by_id(
        self,
        draft_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[DraftReply]:

        query = self.db.query(DraftReply).filter(
            DraftReply.id == draft_id
        )

        if user_id is not None:
            query = query.filter(
                DraftReply.user_id == user_id
            )

        return query.first()

    def get_by_email_id(
        self,
        email_id: int,
        user_id: Optional[int] = None,
    ) -> list[DraftReply]:

        query = self.db.query(DraftReply).filter(
            DraftReply.email_id == email_id
        )

        if user_id is not None:
            query = query.filter(
                DraftReply.user_id == user_id
            )

        return (
            query
            .order_by(DraftReply.version.desc())
            .all()
        )

    def get_latest_draft_for_email(
        self,
        email_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[DraftReply]:

        query = self.db.query(DraftReply).filter(
            DraftReply.email_id == email_id,
            DraftReply.is_current.is_(True),
        )

        if user_id is not None:
            query = query.filter(
                DraftReply.user_id == user_id
            )

        return (
            query
            .order_by(DraftReply.version.desc())
            .first()
        )

    def get_latest_version(
        self,
        email_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[DraftReply]:
        """
        Return the highest version for an email.

        This is different from get_latest_draft_for_email():
        this method is based on version number, not is_current.
        """

        query = self.db.query(DraftReply).filter(
            DraftReply.email_id == email_id
        )

        if user_id is not None:
            query = query.filter(
                DraftReply.user_id == user_id
            )

        return (
            query
            .order_by(DraftReply.version.desc())
            .first()
        )

    def get_by_gmail_draft_id(
        self,
        gmail_draft_id: str,
    ) -> Optional[DraftReply]:

        return (
            self.db.query(DraftReply)
            .filter(
                DraftReply.gmail_draft_id == gmail_draft_id
            )
            .first()
        )

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------

    def update_draft_content(
        self,
        draft_id: int,
        new_content: str,
        user_id: Optional[int] = None,
    ) -> Optional[DraftReply]:

        draft = self.get_by_id(
            draft_id,
            user_id=user_id,
        )

        if not draft:
            logger.warning(
                "Attempted to update non-existent "
                "DraftReply ID %s",
                draft_id,
            )
            return None

        try:
            draft.draft = new_content

            self.db.flush()

            logger.info(
                "Updated DraftReply ID %s content",
                draft_id,
            )

            return draft

        except SQLAlchemyError:
            logger.exception(
                "Failed to update DraftReply ID %s",
                draft_id,
            )
            raise

    def sync_gmail_draft_id(
        self,
        draft_id: int,
        gmail_draft_id: str,
    ) -> Optional[DraftReply]:

        draft = self.get_by_id(draft_id)

        if not draft:
            logger.warning(
                "Attempted Gmail sync on non-existent "
                "DraftReply ID %s",
                draft_id,
            )
            return None

        try:
            draft.gmail_draft_id = gmail_draft_id

            self.db.flush()

            logger.info(
                "Synced Gmail Draft ID '%s' to "
                "DraftReply ID %s",
                gmail_draft_id,
                draft_id,
            )

            return draft

        except SQLAlchemyError:
            logger.exception(
                "Failed to sync Gmail Draft ID "
                "for DraftReply ID %s",
                draft_id,
            )
            raise

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    def delete_draft(
        self,
        draft_id: int,
    ) -> bool:

        draft = self.get_by_id(draft_id)

        if not draft:
            return False

        try:
            self.db.delete(draft)
            self.db.flush()

            logger.info(
                "Deleted DraftReply ID %s",
                draft_id,
            )

            return True

        except SQLAlchemyError:
            logger.exception(
                "Failed to delete DraftReply ID %s",
                draft_id,
            )
            raise