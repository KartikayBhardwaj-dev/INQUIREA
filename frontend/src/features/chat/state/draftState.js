// features/chat/state/draftState.js

export const DRAFT_STATUS = {
  PENDING: "PENDING",
  APPROVED: "APPROVED",
  REJECTED: "REJECTED",
  SENT: "SENT",
};


export function createEmptyDraftState() {
  return {
    draft_id: null,
    email_id: null,
    content: "",
    version: null,
    tone: null,
    approval_status: null,
    gmail_draft_id: null,
    is_sent: false,
    sent_at: null,
  };
}


export function normalizeApprovalStatus(
  status
) {
  if (!status) {
    return null;
  }

  const normalized =
    String(status)
      .trim()
      .toUpperCase();

  switch (normalized) {
    case DRAFT_STATUS.PENDING:
      return DRAFT_STATUS.PENDING;

    case DRAFT_STATUS.APPROVED:
      return DRAFT_STATUS.APPROVED;

    case DRAFT_STATUS.REJECTED:
      return DRAFT_STATUS.REJECTED;

    case DRAFT_STATUS.SENT:
      return DRAFT_STATUS.SENT;

    default:
      return null;
  }
}


export function normalizeDraftState(
  data
) {
  if (
    !data ||
    typeof data !== "object"
  ) {
    return createEmptyDraftState();
  }

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
      data.draft ??
      "",

    version:
      data.version ??
      null,

    tone:
      data.tone ??
      null,

    approval_status:
      normalizeApprovalStatus(
        data.approval_status ??
        data.approvalStatus
      ),

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


/**
 * Merge a backend tool result into
 * the current DraftState.
 *
 * Existing information is preserved when
 * the backend action returns only a partial
 * result.
 */
export function updateDraftState(
  currentState,
  data
) {
  const current =
    currentState ??
    createEmptyDraftState();

  const incoming =
    normalizeDraftState(data);

  return {
    ...current,

    draft_id:
      incoming.draft_id ??
      current.draft_id,

    email_id:
      incoming.email_id ??
      current.email_id,

    content:
      incoming.content ||
      current.content,

    version:
      incoming.version ??
      current.version,

    tone:
      incoming.tone ??
      current.tone,

    approval_status:
      incoming.approval_status ??
      current.approval_status,

    gmail_draft_id:
      incoming.gmail_draft_id ??
      current.gmail_draft_id,

    is_sent:
      incoming.is_sent ||
      current.is_sent,

    sent_at:
      incoming.sent_at ??
      current.sent_at,
  };
}


/**
 * Apply a specific tool action.
 */
export function applyDraftAction(
  currentState,
  action,
  data = {}
) {
  const current =
    currentState ??
    createEmptyDraftState();

  const incoming =
    normalizeDraftState(data);

  switch (action) {
    case "generate_reply":
      return {
        ...current,
        ...updateDraftState(
          current,
          incoming
        ),

        approval_status:
          incoming.approval_status ??
          DRAFT_STATUS.PENDING,

        is_sent: false,
        sent_at: null,
      };

    case "rewrite_reply":
    case "edit_draft":
    case "update_draft":
      return {
        ...updateDraftState(
          current,
          incoming
        ),

        approval_status:
          incoming.approval_status ??
          DRAFT_STATUS.PENDING,

        is_sent: false,
        sent_at: null,
      };

    case "approve_draft":
      return {
        ...updateDraftState(
          current,
          incoming
        ),

        approval_status:
          DRAFT_STATUS.APPROVED,

        is_sent: false,
      };

    case "reject_draft":
      return {
        ...updateDraftState(
          current,
          incoming
        ),

        approval_status:
          DRAFT_STATUS.REJECTED,

        is_sent: false,
      };

    case "send_reply":
      return {
        ...updateDraftState(
          current,
          incoming
        ),

        approval_status:
          DRAFT_STATUS.SENT,

        is_sent: true,

        sent_at:
          incoming.sent_at ??
          new Date().toISOString(),
      };

    case "save_draft":
      return updateDraftState(
        current,
        incoming
      );

    default:
      return updateDraftState(
        current,
        incoming
      );
  }
}