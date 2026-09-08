// ============================================================
// DraftState Model
// ============================================================

export const DRAFT_STATUS = Object.freeze({
  PENDING: "PENDING",
  APPROVED: "APPROVED",
  REJECTED: "REJECTED",
  SENT: "SENT",
});


// ============================================================
// Normalize status
// ============================================================

function normalizeStatus(status) {
  if (!status) {
    return null;
  }

  const normalized =
    String(status)
      .trim()
      .toUpperCase();

  if (
    Object.values(DRAFT_STATUS).includes(
      normalized
    )
  ) {
    return normalized;
  }

  return null;
}


// ============================================================
// Empty draft state
// ============================================================

export function createEmptyDraftState() {
  return {
    draft_id: null,
    email_id: null,

    // Actual LLM-generated reply
    draft: "",

    // Legacy/UI alias
    content: "",

    version: null,

    tone: null,

    approval_status:
      DRAFT_STATUS.PENDING,

    gmail_draft_id: null,

    is_sent: false,

    sent_at: null,
  };
}


// ============================================================
// Create normalized draft state
// ============================================================

export function createDraftState(data = {}) {
  const empty =
    createEmptyDraftState();

  return {
    ...empty,

    draft_id:
      data.draft_id ??
      data.draftId ??
      null,

    email_id:
      data.email_id ??
      data.emailId ??
      null,

    draft:
      data.draft ??
      data.content ??
      data.draft_content ??
      data.body ??
      "",

    content:
      data.draft ??
      data.content ??
      data.draft_content ??
      data.body ??
      "",

    version:
      data.version ??
      null,

    tone:
      data.tone ??
      null,

    approval_status:
      normalizeStatus(
        data.approval_status ??
        data.approvalStatus ??
        data.status
      ) ??
      DRAFT_STATUS.PENDING,

    gmail_draft_id:
      data.gmail_draft_id ??
      data.gmailDraftId ??
      null,

    is_sent:
      Boolean(
        data.is_sent ??
        data.isSent ??
        false
      ),

    sent_at:
      data.sent_at ??
      data.sentAt ??
      null,
  };
}