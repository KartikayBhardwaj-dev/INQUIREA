from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ApprovalRequest(BaseModel):
    """
    Request to approve or reject a draft.
    """

    draft_id: int


class ApprovalResponse(BaseModel):
    """
    Approval status returned to the client.
    """

    draft_id: int
    status: Literal[
        "pending",
        "approved",
        "rejected",
    ]
    message: str