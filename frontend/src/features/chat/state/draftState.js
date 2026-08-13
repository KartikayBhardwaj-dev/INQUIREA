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

export function applyDraftAction(
  currentDraft,
  tool,
  toolResult
) {
  const previous =
    currentDraft ??
    createEmptyDraftState();

  if (
    !tool ||
    !toolResult ||
    typeof toolResult !== "object"
  ) {
    return previous;
  }


  const next = {
    ...previous,
  };


  // ----------------------------------------------------------
  // GENERATE REPLY
  // ----------------------------------------------------------

  if (tool === "generate_reply") {

    return {
      ...previous,

      draft_id:
        firstDefined(
          toolResult.draft_id,
          toolResult.draftId
        ),

      email_id:
        firstDefined(
          toolResult.email_id,
          toolResult.emailId
        ),

      content:
        firstDefined(
          toolResult.content,
          toolResult.draft_content,
          toolResult.body,
          ""
        ),

      version:
        firstDefined(
          toolResult.version,
          1
        ),

      tone:
        firstDefined(
          toolResult.tone,
          "professional"
        ),

      approval_status:
        normalizeStatus(
          toolResult.approval_status ??
          toolResult.status
        ) ??
        DRAFT_STATUS.PENDING,

      gmail_draft_id:
        firstDefined(
          toolResult.gmail_draft_id,
          toolResult.gmailDraftId
        ),

      is_sent:
        Boolean(
          toolResult.is_sent ??
          false
        ),

      sent_at:
        firstDefined(
          toolResult.sent_at,
          toolResult.sentAt
        ),
    };
  }


  // ----------------------------------------------------------
  // REWRITE REPLY
  // ----------------------------------------------------------

  // ----------------------------------------------------------
// REWRITE / REGENERATE REPLY
//
// IMPORTANT:
// Regeneration creates a NEW backend draft version.
// The backend response is authoritative.
//
// Do NOT blindly merge the old draft into the new one.
// ----------------------------------------------------------

if (
  tool === "rewrite_reply" ||
  tool === "regenerate_reply"
) {
  return {
    draft_id:
      firstDefined(
        toolResult.draft_id,
        toolResult.draftId
      ),

    email_id:
      firstDefined(
        toolResult.email_id,
        toolResult.emailId
      ),

    content:
      firstDefined(
        toolResult.content,
        toolResult.draft_content,
        toolResult.body,
        ""
      ),

    version:
      firstDefined(
        toolResult.version,
        1
      ),

    tone:
      firstDefined(
        toolResult.tone,
        "professional"
      ),

    approval_status:
      normalizeStatus(
        toolResult.approval_status ??
        toolResult.status
      ) ??
      DRAFT_STATUS.PENDING,

    gmail_draft_id:
      firstDefined(
        toolResult.gmail_draft_id,
        toolResult.gmailDraftId
      ),

    is_sent:
      Boolean(
        toolResult.is_sent ??
        false
      ),

    sent_at:
      firstDefined(
        toolResult.sent_at,
        toolResult.sentAt
      ),
  };
}

  // ----------------------------------------------------------
  // EDIT DRAFT
  // ----------------------------------------------------------

  if (tool === "edit_draft") {

    return {
      ...previous,

      draft_id:
        firstDefined(
          toolResult.draft_id,
          toolResult.draftId,
          previous.draft_id
        ),

      email_id:
        firstDefined(
          toolResult.email_id,
          toolResult.emailId,
          previous.email_id
        ),

      content:
        firstDefined(
          toolResult.content,
          toolResult.draft_content,
          toolResult.body,
          previous.content
        ),

      version:
        firstDefined(
          toolResult.version,
          previous.version
            ? previous.version + 1
            : 1
        ),

      approval_status:
        DRAFT_STATUS.PENDING,

      is_sent: false,

      sent_at: null,
    };
  }


  // ----------------------------------------------------------
  // APPROVE
  // ----------------------------------------------------------

  // ----------------------------------------------------------
// APPROVE
// ----------------------------------------------------------

if (tool === "approve_draft") {

  return {
    ...previous,

    draft_id:
      firstDefined(
        toolResult.draft_id,
        toolResult.draftId,
        previous.draft_id
      ),

    approval_status:
      normalizeStatus(
        toolResult.approval_status ??
        toolResult.status
      ) ??
      DRAFT_STATUS.APPROVED,

    is_sent:
      Boolean(
        toolResult.is_sent ??
        false
      ),

    sent_at:
      firstDefined(
        toolResult.sent_at,
        toolResult.sentAt,
        null
      ),
  };
}

  // ----------------------------------------------------------
  // REJECT
  // ----------------------------------------------------------

  if (tool === "reject_draft") {

    return {
      ...previous,

      draft_id:
        firstDefined(
          toolResult.draft_id,
          toolResult.draftId,
          previous.draft_id
        ),

      approval_status:
        DRAFT_STATUS.REJECTED,

      is_sent: false,

      sent_at: null,
    };
  }


  // ----------------------------------------------------------
  // SAVE
  // ----------------------------------------------------------

  if (tool === "save_draft") {

    return {
      ...previous,

      draft_id:
        firstDefined(
          toolResult.draft_id,
          toolResult.draftId,
          previous.draft_id
        ),

      gmail_draft_id:
        firstDefined(
          toolResult.gmail_draft_id,
          toolResult.gmailDraftId,
          previous.gmail_draft_id
        ),
    };
  }


  // ----------------------------------------------------------
  // SEND
  // ----------------------------------------------------------

  if (tool === "send_reply") {

    return {
      ...previous,

      draft_id:
        firstDefined(
          toolResult.draft_id,
          toolResult.draftId,
          previous.draft_id
        ),

      approval_status:
        DRAFT_STATUS.SENT,

      is_sent: true,

      sent_at:
        firstDefined(
          toolResult.sent_at,
          toolResult.sentAt,
          new Date().toISOString()
        ),
    };
  }


  // Unknown action → don't touch draft.
  return next;
}


export {
  DRAFT_STATUS,
  createEmptyDraftState,
};