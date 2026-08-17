"use client";

import DraftCard from "./DraftCard";


export default function ChatActionRenderer({
  action,
  draft,

  onEdit,
  onRegenerate,
  onApprove,
  onReject,
  onSaveToGmail,
  onSend,

  isLoading,
  loadingAction,
  getLoadingLabel,
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

        onEdit={
          onEdit
        }

        onRegenerate={
          onRegenerate
        }

        onApprove={
          onApprove
        }

        onReject={
          onReject
        }

        onSaveToGmail={
          onSaveToGmail
        }

        onSend={
          onSend
        }

        isLoading={
          isLoading
        }

        loadingAction={
          loadingAction
        }

        getLoadingLabel={
          getLoadingLabel
        }
      />
    );
  }


  return null;
}