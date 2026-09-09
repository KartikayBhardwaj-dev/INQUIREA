"use client";

import DraftCard from "./DraftCard";

export default function ChatActionRenderer({
  action,
  draft,
  onApprove,
  onReject,
  onSend,
  isLoading,
  loadingAction,
  getLoadingLabel,
}) {
  if (!action) return null;

  if (action.type === "draft") {
    return (
      <DraftCard
        draft={draft}
        onApprove={onApprove}
        onReject={onReject}
        onSend={onSend}
        isLoading={isLoading}
        loadingAction={loadingAction}
        getLoadingLabel={getLoadingLabel}
      />
    );
  }

  return null;
}