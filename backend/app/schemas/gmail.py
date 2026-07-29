from pydantic import BaseModel


# ---------------------------------------------------------
# Save Draft
# ---------------------------------------------------------

class SaveDraftRequest(BaseModel):
    draft_id: int


class SaveDraftResponse(BaseModel):
    status: str
    draft_id: int
    gmail_draft_id: str


# ---------------------------------------------------------
# Update Draft
# ---------------------------------------------------------

class UpdateDraftRequest(BaseModel):
    draft_id: int


class UpdateDraftResponse(BaseModel):
    status: str
    draft_id: int
    gmail_draft_id: str


# ---------------------------------------------------------
# Send Reply
# ---------------------------------------------------------

class SendReplyRequest(BaseModel):
    draft_id: int


class SendReplyResponse(BaseModel):
    status: str
    draft_id: int
    message_id: str


# ---------------------------------------------------------
# Generic Sync Response
# ---------------------------------------------------------

class SyncResponse(BaseModel):
    status: str
    message: str