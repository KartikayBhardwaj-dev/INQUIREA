export const DRAFT_STATUS = {
  PENDING: "PENDING",
  APPROVED: "APPROVED",
  REJECTED: "REJECTED",
  SENT: "SENT",
};


export function createDraftState(data = {}) {
  return {
    draft_id:
      data.draft_id ??
      data.draftId ??
      null,

    email_id:
      data.email_id ??
      data.emailId ??
      null,

    content:
      data.content ??
      data.body ??
      data.text ??
      "",

    version:
      data.version ??
      1,

    tone:
      data.tone ??
      "professional",

    approval_status:
      data.approval_status ??
      data.approvalStatus ??
      DRAFT_STATUS.PENDING,

    gmail_draft_id:
      data.gmail_draft_id ??
      data.gmailDraftId ??
      null,

    is_sent:
      data.is_sent ??
      data.isSent ??
      false,

    sent_at:
      data.sent_at ??
      data.sentAt ??
      null,
  };
}


export function updateDraftState(
  currentDraft,
  data = {}
) {
  return {
    ...currentDraft,
    ...createDraftState({
      ...currentDraft,
      ...data,
    }),
  };
}