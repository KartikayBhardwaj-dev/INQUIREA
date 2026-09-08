from __future__ import annotations

from backend.app.services.approval_service import ApprovalService
from backend.app.services.gmail_action_service import GmailActionService
from backend.app.tools.approval_tools import ApprovalTools
from backend.app.tools.base_tool import BaseTool

from backend.app.models.approval import ApprovalStatus


class ApproveDraftTool(BaseTool):

    name = "approve_draft"

    async def execute(
        self,
        **kwargs,
    ):
        # =====================================================
        # VALIDATE INPUT
        # =====================================================

        db = kwargs.get("db")
        draft_id = kwargs.get("draft_id")
        user_id = kwargs.get("user_id")

        if db is None:
            raise ValueError(
                "Database session missing."
            )

        if draft_id is None:
            raise ValueError(
                "draft_id is required."
            )

        if user_id is None:
            raise ValueError(
                "user_id is required."
            )

        # =====================================================
        # APPROVE DRAFT
        # =====================================================

        approval_service = ApprovalService(db)
        approval_tools = ApprovalTools(approval_service)

        approval = approval_tools.approve_draft(
            draft_id=draft_id,
            user_id=user_id,
        )

        # =====================================================
        # VERIFY APPROVAL
        # =====================================================

        if approval is None:
            raise ValueError(
                f"Approval for draft {draft_id} could not be created."
            )

        if approval.status != ApprovalStatus.APPROVED.value:
            raise ValueError(
                f"Draft {draft_id} approval failed. "
                f"Current status: {approval.status}"
            )

        # =====================================================
        # CREATE / UPDATE GMAIL DRAFT
        # =====================================================
        #
        # Approval now means:
        #   1. Local approval = approved
        #   2. Gmail draft is created
        #   3. gmail_draft_id is saved locally
        #
        # GmailActionService.save_draft() handles all of this.
        # =====================================================

        gmail_service = GmailActionService(db)

        gmail_result = await gmail_service.save_draft(
            draft_id=approval.draft_reply_id,
            user_id=user_id,
        )

        # =====================================================
        # RETURN FRONTEND-FRIENDLY RESPONSE
        # =====================================================

        return {
            "draft_id": approval.draft_reply_id,
            "approval_status": approval.status,
            "gmail_draft_id": gmail_result["gmail_draft_id"],
            "can_send": (
                approval.status
                == ApprovalStatus.APPROVED.value
            ),
            "message": "Draft approved and saved to Gmail.",
        }