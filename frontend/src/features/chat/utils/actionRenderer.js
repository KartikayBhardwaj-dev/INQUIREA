import {
  createDraftState,
  DRAFT_STATUS,
} from "../models/draftState";


export function normalizeToolAction(
  response,
  currentDraft = null
) {
  const tool =
    response?.tool ?? null;

  const toolResult =
    response?.tool_result ??
    null;

  if (!tool) {
    return null;
  }


  // --------------------------------------------------
  // GENERATE REPLY
  // --------------------------------------------------

  if (tool === "generate_reply") {
    if (!toolResult) {
      return null;
    }

    const draft = createDraftState({
      ...toolResult,

      approval_status:
        toolResult.approval_status ??
        DRAFT_STATUS.PENDING,

      is_sent:
        toolResult.is_sent ??
        false,
    });

    return {
      type: "draft",
      action: "generate_reply",
      draft,
    };
  }


  // --------------------------------------------------
  // REWRITE REPLY
  // --------------------------------------------------

  if (tool === "rewrite_reply") {
    if (!toolResult) {
      return null;
    }

    const draft = createDraftState({
      ...(currentDraft ?? {}),
      ...toolResult,

      approval_status:
        toolResult.approval_status ??
        currentDraft?.approval_status ??
        DRAFT_STATUS.PENDING,

      is_sent:
        toolResult.is_sent ??
        currentDraft?.is_sent ??
        false,
    });

    return {
      type: "draft",
      action: "rewrite_reply",
      draft,
    };
  }


  // --------------------------------------------------
  // EDIT DRAFT
  // --------------------------------------------------

  if (tool === "edit_draft") {
    if (!toolResult) {
      return null;
    }

    const draft = createDraftState({
      ...(currentDraft ?? {}),
      ...toolResult,
    });

    return {
      type: "draft",
      action: "edit_draft",
      draft,
    };
  }


  // --------------------------------------------------
  // APPROVE
  // --------------------------------------------------

  if (tool === "approve_draft") {
    const draft = createDraftState({
      ...(currentDraft ?? {}),
      ...(toolResult ?? {}),

      approval_status:
        DRAFT_STATUS.APPROVED,

      is_sent:
        currentDraft?.is_sent ??
        false,
    });

    return {
      type: "draft",
      action: "approve_draft",
      draft,
    };
  }


  // --------------------------------------------------
  // REJECT
  // --------------------------------------------------

  if (tool === "reject_draft") {
    const draft = createDraftState({
      ...(currentDraft ?? {}),
      ...(toolResult ?? {}),

      approval_status:
        DRAFT_STATUS.REJECTED,

      is_sent:
        false,
    });

    return {
      type: "draft",
      action: "reject_draft",
      draft,
    };
  }


  // --------------------------------------------------
  // SAVE DRAFT
  // --------------------------------------------------

  if (tool === "save_draft") {
    const draft = createDraftState({
      ...(currentDraft ?? {}),
      ...(toolResult ?? {}),
    });

    return {
      type: "draft",
      action: "save_draft",
      draft,
    };
  }


  // --------------------------------------------------
  // UPDATE DRAFT
  // --------------------------------------------------

  if (tool === "update_draft") {
    const draft = createDraftState({
      ...(currentDraft ?? {}),
      ...(toolResult ?? {}),
    });

    return {
      type: "draft",
      action: "update_draft",
      draft,
    };
  }


  // --------------------------------------------------
  // SEND REPLY
  // --------------------------------------------------

  if (tool === "send_reply") {
    const draft = createDraftState({
      ...(currentDraft ?? {}),
      ...(toolResult ?? {}),

      approval_status:
        DRAFT_STATUS.APPROVED,

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


  // --------------------------------------------------
  // UNKNOWN TOOL
  // --------------------------------------------------

  return {
    type: "tool",
    action: tool,
    result: toolResult,
  };
}