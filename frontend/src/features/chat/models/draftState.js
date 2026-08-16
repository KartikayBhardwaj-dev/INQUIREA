// ============================================================
// DraftState Model
// ============================================================

export const DRAFT_STATUS = Object.freeze({
  PENDING: "PENDING",
  APPROVED: "APPROVED",
  REJECTED: "REJECTED",
  SENT: "SENT",
});


export function createEmptyDraftState() {
  return {
  draft_id: null,
  email_id: null,

  content: "",

  version: null,

  tone: null,

  // Approval is independent from Gmail persistence.
  approval_status:
    DRAFT_STATUS.PENDING,

  // null = not saved to Gmail.
  gmail_draft_id: null,

  is_sent: false,

  sent_at: null,
};
}