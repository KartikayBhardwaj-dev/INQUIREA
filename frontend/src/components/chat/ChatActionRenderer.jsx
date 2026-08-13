"use client";

import DraftCard from "./DraftCard";


export default function ChatActionRenderer({
  action,
  draft,

  onEdit,
  onRegenerate,
  onApprove,
  onReject,
  onSend,

  isLoading,
}) {

  if (!action) {
    return null;
  }


  // ============================================================
  // Draft action
  // ============================================================

  if (
    action.type === "draft"
  ) {

    return (
      <DraftCard
        draft={draft}
        onEdit={onEdit}
        onRegenerate={onRegenerate}
        onApprove={onApprove}
        onReject={onReject}
        onSend={onSend}
        isLoading={isLoading}
      />
    );
  }


  return null;
}