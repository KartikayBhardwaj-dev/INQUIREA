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
    """

    def __init__(self, db: Session):
        self.db = db

    def create_draft(
        self,
        email_id: int,
        content: str,
        user_id: Optional[int] = None,
        tone: str = "professional",
        gmail_draft_id: Optional[str] = None,
    ) -> DraftReply:
        try:
            # Deactivate previous current drafts for this email
            self.db.query(DraftReply).filter(
                DraftReply.email_id == email_id,
                DraftReply.is_current == True, # noqa: E712
            ).update({"is_current": False}, synchronize_session=False)

            draft = DraftReply(
                email_id=email_id,
                user_id=user_id,
                draft=content,
                tone=tone,
                gmail_draft_id=gmail_draft_id,
                version=1,
                is_current=True,
            )
            self.db.add(draft)
            self.db.flush()
            logger.info("Created DraftReply ID %s for Email ID %s", draft.id, email_id)
            return draft
        except SQLAlchemyError:
            logger.exception("Failed to create DraftReply for Email ID %s", email_id)
            raise

    def get_by_id(self, draft_id: int, user_id: Optional[int] = None) -> Optional[DraftReply]:
        query = self.db.query(DraftReply).filter(DraftReply.id == draft_id)
        if user_id is not None:
            query = query.filter(DraftReply.user_id == user_id)
        return query.first()

    def get_by_email_id(self, email_id: int, user_id: Optional[int] = None) -> list[DraftReply]:
        query = self.db.query(DraftReply).filter(DraftReply.email_id == email_id)
        if user_id is not None:
            query = query.filter(DraftReply.user_id == user_id)
        return query.order_by(DraftReply.version.desc()).all()

    def get_latest_draft_for_email(self, email_id: int, user_id: Optional[int] = None) -> Optional[DraftReply]:
        query = self.db.query(DraftReply).filter(
            DraftReply.email_id == email_id,
            DraftReply.is_current == True, # noqa: E712
        )
        if user_id is not None:
            query = query.filter(DraftReply.user_id == user_id)
        return query.first()

    def get_by_gmail_draft_id(self, gmail_draft_id: str) -> Optional[DraftReply]:
        return self.db.query(DraftReply).filter(DraftReply.gmail_draft_id == gmail_draft_id).first()

    def update_draft_content(
        self,
        draft_id: int,
        new_content: str,
        user_id: Optional[int] = None,
    ) -> Optional[DraftReply]:
        draft = self.get_by_id(draft_id, user_id=user_id)
        if not draft:
            logger.warning("Attempted to update non-existent DraftReply ID %s", draft_id)
            return None

        try:
            draft.draft = new_content
            self.db.flush()
            logger.info("Updated DraftReply ID %s content", draft_id)
            return draft
        except SQLAlchemyError:
            logger.exception("Failed to update DraftReply ID %s", draft_id)
            raise

    def sync_gmail_draft_id(self, draft_id: int, gmail_draft_id: str) -> Optional[DraftReply]:
        draft = self.get_by_id(draft_id)
        if not draft:
            logger.warning("Attempted Gmail sync on non-existent DraftReply ID %s", draft_id)
            return None

        try:
            draft.gmail_draft_id = gmail_draft_id
            self.db.flush()
            logger.info("Synced Gmail Draft ID '%s' to DraftReply ID %s", gmail_draft_id, draft_id)
            return draft
        except SQLAlchemyError:
            logger.exception("Failed to sync Gmail Draft ID for DraftReply ID %s", draft_id)
            raise

    def delete_draft(self, draft_id: int) -> bool:
        draft = self.get_by_id(draft_id)
        if not draft:
            return False

        try:
            self.db.delete(draft)
            self.db.flush()
            logger.info("Deleted DraftReply ID %s", draft_id)
            return True
        except SQLAlchemyError:
            logger.exception("Failed to delete DraftReply ID %s", draft_id)
            raise