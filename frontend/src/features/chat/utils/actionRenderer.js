import {
  createDraftState,
  DRAFT_STATUS,
} from "../models/draftState";


// ============================================================
// Normalize backend tool action
// ============================================================

export function normalizeToolAction(
  response,
  currentDraft = null
) {
  const tool =
    response?.tool ??
    null;

  const toolResult =
    response?.tool_result ??
    response?.toolResult ??
    null;


  if (!tool) {
    return null;
  }


  // ----------------------------------------------------------
  // GENERATE REPLY
  // ----------------------------------------------------------

  if (tool === "generate_reply") {

    if (!toolResult) {
      return null;
    }

    const draft =
      createDraftState({
        ...toolResult,

        approval_status:
          toolResult.approval_status ??
          toolResult.approvalStatus ??
          DRAFT_STATUS.PENDING,

        is_sent:
          toolResult.is_sent ??
          toolResult.isSent ??
          false,
      });

    return {
      type: "draft",
      action: "generate_reply",
      draft,
    };
  }


  // ----------------------------------------------------------
  // REWRITE / REGENERATE REPLY
  // ----------------------------------------------------------

  if (
    tool === "rewrite_reply" ||
    tool === "regenerate_reply"
  ) {

    if (!toolResult) {
      return null;
    }

    const draft =
      createDraftState({
        ...toolResult,

        approval_status:
          toolResult.approval_status ??
          toolResult.approvalStatus ??
          DRAFT_STATUS.PENDING,

        // A rewritten version must not inherit
        // the previous Gmail/send state.
        gmail_draft_id: null,

        is_sent: false,

        sent_at: null,
      });

    return {
      type: "draft",
      action: tool,
      draft,
    };
  }


  // ----------------------------------------------------------
  // EDIT DRAFT
  // ----------------------------------------------------------

  if (tool === "edit_draft") {

    if (!toolResult) {
      return null;
    }

    const draft =
      createDraftState({
        ...(currentDraft ?? {}),
        ...toolResult,

        // Editing creates a new unsaved version.
        approval_status:
          DRAFT_STATUS.PENDING,

        gmail_draft_id:
          null,

        is_sent:
          false,

        sent_at:
          null,
      });

    return {
      type: "draft",
      action: "edit_draft",
      draft,
    };
  }


  // ----------------------------------------------------------
  // APPROVE
  // ----------------------------------------------------------

  if (tool === "approve_draft") {

    const draft =
      createDraftState({
        ...(currentDraft ?? {}),
        ...(toolResult ?? {}),

        approval_status:
          DRAFT_STATUS.APPROVED,

        is_sent:
          false,

        sent_at:
          null,
      });

    return {
      type: "draft",
      action: "approve_draft",
      draft,
    };
  }


  // ----------------------------------------------------------
  // REJECT
  // ----------------------------------------------------------

  if (tool === "reject_draft") {

    const draft =
      createDraftState({
        ...(currentDraft ?? {}),
        ...(toolResult ?? {}),

        approval_status:
          DRAFT_STATUS.REJECTED,

        gmail_draft_id:
          null,

        is_sent:
          false,

        sent_at:
          null,
      });

    return {
      type: "draft",
      action: "reject_draft",
      draft,
    };
  }


  // ----------------------------------------------------------
  // SAVE DRAFT
  // ----------------------------------------------------------

  if (tool === "save_draft") {

    const draft =
      createDraftState({
        ...(currentDraft ?? {}),
        ...(toolResult ?? {}),

        // Saving to Gmail does NOT approve the draft.
        approval_status:
          currentDraft?.approval_status ??
          DRAFT_STATUS.APPROVED,
      });

    return {
      type: "draft",
      action: "save_draft",
      draft,
    };
  }


  // ----------------------------------------------------------
  // UPDATE DRAFT
  // ----------------------------------------------------------

  if (tool === "update_draft") {

    const draft =
      createDraftState({
        ...(currentDraft ?? {}),
        ...(toolResult ?? {}),
      });

    return {
      type: "draft",
      action: "update_draft",
      draft,
    };
  }


  // ----------------------------------------------------------
  // SEND REPLY
  // ----------------------------------------------------------

  if (tool === "send_reply") {

    const draft =
      createDraftState({
        ...(currentDraft ?? {}),
        ...(toolResult ?? {}),

        approval_status:
          DRAFT_STATUS.SENT,

        is_sent:
          true,

        sent_at:
          toolResult?.sent_at ??
          toolResult?.sentAt ??
          new Date().toISOString(),
      });

    return {
      type: "draft",
      action: "send_reply",
      draft,
    };
  }


  // ----------------------------------------------------------
  // UNKNOWN TOOL
  // ----------------------------------------------------------

  return {
    type: "tool",
    action: tool,
    result: toolResult,
  };
}