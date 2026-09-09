import {
  DRAFT_STATUS,
  createEmptyDraftState,
} from "../models/draftState";


// ============================================================
// Helpers
// ============================================================

function firstDefined(...values) {
  for (const value of values) {
    if (
      value !== undefined &&
      value !== null
    ) {
      return value;
    }
  }

  return null;
}


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
// Apply backend action
// ============================================================

export function applyDraftAction(currentDraft, tool, toolResult) {
  const previous = currentDraft ?? createEmptyDraftState();
  const result = toolResult ?? {};

  switch (tool) {
    case "generate_reply": {
      const content =
        result.draft ??
        result.content ??
        result.draft_content ??
        "";

      return {
        ...previous,
        draft_id: result.draft_id ?? previous.draft_id,
        email_id: result.email_id ?? previous.email_id,
        draft: content,
        content,
        version: result.version ?? 1,
        tone: result.tone ?? previous.tone,
        approval_status:
          result.approval_status ?? DRAFT_STATUS.PENDING,
        gmail_draft_id: result.gmail_draft_id ?? null,
        is_sent: false,
        sent_at: null,
      };
    }

    case "rewrite_reply":
    case "regenerate_reply": {
      const content =
        result.draft ??
        result.content ??
        result.draft_content ??
        "";

      return {
        ...previous,
        draft_id: result.draft_id ?? previous.draft_id,
        email_id: result.email_id ?? previous.email_id,
        draft: content,
        content,
        version: result.version ?? previous.version,
        tone: result.tone ?? previous.tone,
        approval_status:
          result.approval_status ?? DRAFT_STATUS.PENDING,
        gmail_draft_id: null,
        is_sent: false,
        sent_at: null,
      };
    }

    case "edit_draft": {
      const content =
        result.draft ??
        result.content ??
        result.draft_content ??
        "";

      return {
        ...previous,
        draft_id: result.draft_id ?? previous.draft_id,
        email_id: result.email_id ?? previous.email_id,
        draft: content,
        content,
        version: result.version ?? previous.version,
        tone: result.tone ?? previous.tone,
        approval_status: DRAFT_STATUS.PENDING,
        gmail_draft_id: null,
        is_sent: false,
        sent_at: null,
      };
    }

    case "update_draft": {
      const content =
        result.draft ??
        result.content ??
        result.draft_content ??
        previous.draft ??
        previous.content ??
        "";

      return {
        ...previous,
        draft_id: result.draft_id ?? previous.draft_id,
        email_id: result.email_id ?? previous.email_id,
        draft: content,
        content,
        version: result.version ?? previous.version,
        tone: result.tone ?? previous.tone,
        approval_status:
          result.approval_status ?? DRAFT_STATUS.PENDING,
        gmail_draft_id:
          result.gmail_draft_id ?? previous.gmail_draft_id,
        is_sent: false,
        sent_at: null,
      };
    }

    case "approve_draft": {
      const content =
        result.draft ??
        result.content ??
        result.draft_content ??
        previous.draft ??
        previous.content ??
        "";

      return {
        ...previous,
        draft_id: result.draft_id ?? previous.draft_id,
        email_id: result.email_id ?? previous.email_id,
        draft: content,
        content,
        version: result.version ?? previous.version,
        tone: result.tone ?? previous.tone,
        approval_status: DRAFT_STATUS.APPROVED,
        gmail_draft_id:
          result.gmail_draft_id ?? previous.gmail_draft_id,
        is_sent: false,
        sent_at: null,
      };
    }

    case "reject_draft": {
      return {
        ...previous,
        draft_id: result.draft_id ?? previous.draft_id,
        email_id: result.email_id ?? previous.email_id,
        approval_status: DRAFT_STATUS.REJECTED,
        gmail_draft_id: null,
        is_sent: false,
        sent_at: null,
      };
    }

    case "save_draft": {
      return {
        ...previous,
        draft_id: result.draft_id ?? previous.draft_id,
        gmail_draft_id:
          result.gmail_draft_id ?? previous.gmail_draft_id,
      };
    }

    case "send_reply": {
      return {
        ...previous,
        draft_id: result.draft_id ?? previous.draft_id,
        email_id: result.email_id ?? previous.email_id,
        approval_status: DRAFT_STATUS.SENT,
        gmail_draft_id:
          result.gmail_draft_id ?? previous.gmail_draft_id,
        is_sent: true,
        sent_at: result.sent_at ?? new Date().toISOString(),
      };
    }

    default:
      return previous;
  }
}
export {
  DRAFT_STATUS,
  createEmptyDraftState,
};