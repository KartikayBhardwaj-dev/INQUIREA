
"use client";

import { useState } from "react";

const DRAFT_STATUS = {
  PENDING: "pending",
  APPROVED: "approved",
  REJECTED: "rejected",
  SENT: "sent",
};

export default function DraftCard({
  draft,
  onApprove,
  onReject,
  onSend,
  isLoading,
  loadingAction,
  getLoadingLabel,
}) {
  console.log("DRAFT CARD RECEIVED:", draft);
  const [showSendConfirmation, setShowSendConfirmation] =
    useState(false);

  if (!draft) {
    return null;
  }

  // ============================================================
  // STATUS
  // ============================================================

  const approvalStatus =
    draft.approval_status?.toLowerCase?.() ||
    DRAFT_STATUS.PENDING;

  const isSent =
    Boolean(draft.is_sent) ||
    approvalStatus === DRAFT_STATUS.SENT;

  const isApproved =
    approvalStatus === DRAFT_STATUS.APPROVED;

  const isRejected =
    approvalStatus === DRAFT_STATUS.REJECTED;

  const isPending =
    approvalStatus === DRAFT_STATUS.PENDING &&
    !isSent;

  const isSavedToGmail =
    Boolean(draft.gmail_draft_id);

  // ============================================================
  // LOADING STATE
  // ============================================================

  const loadingLabel = getLoadingLabel
    ? getLoadingLabel(loadingAction)
    : null;

  // ============================================================
  // SEND CONFIRMATION
  // ============================================================

  const handleConfirmSend = async () => {
    if (!isApproved) {
      return;
    }

    if (!draft.gmail_draft_id) {
      return;
    }

    const result = await onSend?.();

    if (result !== null && result !== false) {
      setShowSendConfirmation(false);
    }
  };

  // ============================================================
  // DISPLAY DATA
  // ============================================================

  const recipient =
    draft.recipient ||
    draft.to ||
    draft.email?.sender ||
    draft.email?.from ||
    "recipient";

  const subject =
    draft.subject ||
    draft.email?.subject ||
    "this email";

  const content =
    draft.draft ||
    draft.content ||
    "";

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <>
      <div className="w-full max-w-2xl rounded-xl border border-white/10 bg-white/[0.04] p-4 shadow-sm">

        {/* ======================================================
            HEADER
        ====================================================== */}

        <div className="mb-3 flex items-center justify-between gap-3">

          <div className="min-w-0">

            <div className="text-xs font-medium uppercase tracking-wide text-white/40">
              Draft Reply
            </div>

            <div className="mt-1 truncate text-sm font-medium text-white/90">
              {subject}
            </div>

          </div>


          {/* ====================================================
              STATUS BADGE
          ==================================================== */}

          {isSent ? (

            <span className="shrink-0 rounded-full border border-white/10 bg-white/10 px-2.5 py-1 text-xs font-medium text-white/80">
              ✓ Sent
            </span>

          ) : isApproved ? (

            <span className="shrink-0 rounded-full border border-white/10 bg-white/10 px-2.5 py-1 text-xs font-medium text-white/80">
              ✓ Approved
            </span>

          ) : isRejected ? (

            <span className="shrink-0 rounded-full border border-white/10 bg-white/10 px-2.5 py-1 text-xs font-medium text-white/60">
              Rejected
            </span>

          ) : (

            <span className="shrink-0 rounded-full border border-white/10 bg-white/10 px-2.5 py-1 text-xs font-medium text-white/70">
              Pending
            </span>

          )}

        </div>


        {/* ======================================================
            RECIPIENT
        ====================================================== */}

        <div className="mb-3 text-xs text-white/50">

          To:{" "}

          <span className="text-white/70">
            {recipient}
          </span>

        </div>


        {/* ======================================================
            DRAFT CONTENT
        ====================================================== */}

        <div className="rounded-lg border border-white/10 bg-black/20 p-4">

          <div className="whitespace-pre-wrap text-sm leading-6 text-white/85">
            {content}
          </div>

        </div>


        {/* ======================================================
            GMAIL STATUS
        ====================================================== */}

        {isApproved &&
          isSavedToGmail &&
          !isSent && (

            <div className="mt-3 flex items-center gap-2 text-xs text-white/50">

              <span>✓</span>

              <span>
                Saved to Gmail
              </span>

            </div>

          )}


        {/* ======================================================
            ACTIONS
        ====================================================== */}

        <div className="mt-4 flex flex-wrap items-center gap-2">

          {/* ====================================================
              PENDING → APPROVE
          ==================================================== */}

          {isPending && (

            <button
              type="button"
              disabled={isLoading}
              onClick={() => onApprove?.()}
              className="rounded-lg bg-white px-3 py-2 text-xs font-medium text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loadingAction === "approveDraft"
                ? loadingLabel || "Approving..."
                : "Approve"}
            </button>

          )}


          {/* ====================================================
              PENDING → REJECT
          ==================================================== */}

          {isPending && (

            <button
              type="button"
              disabled={isLoading}
              onClick={() => onReject?.()}
              className="rounded-lg border border-white/10 bg-white/[0.05] px-3 py-2 text-xs font-medium text-white/70 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loadingAction === "rejectDraft"
                ? loadingLabel || "Rejecting..."
                : "Reject"}
            </button>

          )}


          {/* ====================================================
              APPROVED + GMAIL DRAFT → SEND
          ==================================================== */}

          {isApproved &&
            !isSent && (

            <button
              type="button"
              disabled={
                isLoading ||
                !isSavedToGmail
              }
              onClick={() =>
                setShowSendConfirmation(true)
              }
              className="rounded-lg bg-white px-3 py-2 text-xs font-medium text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loadingAction === "sendDraft"
                ? loadingLabel || "Sending..."
                : "Send"}
            </button>

          )}

        </div>

      </div>


      {/* ========================================================
          SEND CONFIRMATION MODAL
      ======================================================== */}

      {showSendConfirmation && (

        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">

          <div className="w-full max-w-md rounded-xl border border-white/10 bg-[#111111] p-5 shadow-2xl">

            {/* ==================================================
                MODAL HEADER
            ================================================== */}

            <div className="mb-4">

              <h3 className="text-base font-semibold text-white">
                Send this reply?
              </h3>

              <p className="mt-1 text-sm leading-5 text-white/50">

                This will send the approved draft to{" "}

                <span className="text-white/80">
                  {recipient}
                </span>

                .

              </p>

            </div>


            {/* ==================================================
                EMAIL DETAILS
            ================================================== */}

            <div className="mb-4 rounded-lg border border-white/10 bg-white/[0.03] p-3">

              <div className="text-xs text-white/40">
                Subject
              </div>

              <div className="mt-1 text-sm text-white/80">
                {subject}
              </div>

            </div>


            {/* ==================================================
                WARNING
            ================================================== */}

            <div className="mb-5 rounded-lg border border-white/10 bg-white/[0.03] p-3">

              <p className="text-xs leading-5 text-white/50">

                Once sent, this reply will be delivered through
                Gmail and cannot be undone from INQUIREA.

              </p>

            </div>


            {/* ==================================================
                MODAL ACTIONS
            ================================================== */}

            <div className="flex justify-end gap-2">

              <button
                type="button"
                disabled={isLoading}
                onClick={() =>
                  setShowSendConfirmation(false)
                }
                className="rounded-lg border border-white/10 bg-white/[0.05] px-3 py-2 text-xs font-medium text-white/70 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Cancel
              </button>


              <button
                type="button"
                disabled={
                  isLoading ||
                  !isApproved ||
                  !draft.gmail_draft_id
                }
                onClick={handleConfirmSend}
                className="rounded-lg bg-white px-3 py-2 text-xs font-medium text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {loadingAction === "sendDraft"
                  ? loadingLabel || "Sending..."
                  : "Confirm Send"}
              </button>

            </div>

          </div>

        </div>

      )}

    </>
  );
}