"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  DRAFT_STATUS,
} from "@/features/chat/models/draftState";


export default function DraftCard({
  draft,
  onEdit,
  onRegenerate,
  onApprove,
  onReject,
  onSaveToGmail,
  onSend,

  isLoading = false,
  loadingAction = null,
  getLoadingLabel,
}) {

  const [
    isEditing,
    setIsEditing,
  ] = useState(false);


  const [
    editedContent,
    setEditedContent,
  ] = useState(
    draft?.content ?? ""
  );


  // ============================================================
  // TASK 35 — Send confirmation modal
  // ============================================================

  const [
    showSendConfirmation,
    setShowSendConfirmation,
  ] = useState(false);


  useEffect(() => {

    if (!isEditing) {

      setEditedContent(
        draft?.content ?? ""
      );
    }

  }, [
    draft?.content,
    isEditing,
  ]);


  if (!draft) {
    return null;
  }


  if (!draft.draft_id) {
    return null;
  }


  const status =
    draft.is_sent
      ? DRAFT_STATUS.SENT
      : draft.approval_status ??
        DRAFT_STATUS.PENDING;


  // ============================================================
  // TASK 37 — Action helpers
  // ============================================================

  const isEditingAction =
    loadingAction === "editDraft";


  const isRegenerating =
    loadingAction === "regenerateDraft";


  const isApproving =
    loadingAction === "approveDraft";


  const isRejecting =
    loadingAction === "rejectDraft";


  const isSavingToGmail =
    loadingAction ===
    "saveDraftToGmail";


  const isSending =
    loadingAction ===
    "sendDraft";


  const loadingText =
    getLoadingLabel?.(
      loadingAction
    ) ??
    "Loading...";


  // ============================================================
  // EDIT MODE
  // ============================================================

  if (isEditing) {

    return (
      <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4">

        <div className="mb-3 flex items-center justify-between">

          <div>

            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/40">
              Edit Draft
            </p>

            <p className="mt-1 text-xs text-white/30">
              Draft #{draft.draft_id}
            </p>

          </div>

        </div>


        <textarea
          value={editedContent}
          onChange={(event) =>
            setEditedContent(
              event.target.value
            )
          }
          rows={8}
          className="w-full resize-y rounded-xl border border-white/10 bg-black/20 p-3 text-sm leading-6 text-white outline-none transition focus:border-white/25 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={isLoading}
          autoFocus
        />


        <div className="mt-3 flex gap-2">

          <button
            type="button"
            disabled={
              isLoading ||
              !editedContent.trim()
            }
            onClick={async () => {

              const content =
                editedContent.trim();


              const result =
                await onEdit?.(
                  content
                );


              /*
               * Keep edit mode open if the request failed
               * or was rejected.
               */
              if (result !== null) {
                setIsEditing(false);
              }

            }}
            className="rounded-lg bg-white px-3 py-2 text-xs font-medium text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
          >

            {isEditingAction
              ? "Saving..."
              : "Save"}

          </button>


          <button
            type="button"
            disabled={isLoading}
            onClick={() => {

              setEditedContent(
                draft.content ?? ""
              );

              setIsEditing(false);

            }}
            className="rounded-lg border border-white/10 px-3 py-2 text-xs text-white/60 transition hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            Cancel
          </button>

        </div>

      </div>
    );
  }


  // ============================================================
  // SENT
  // ============================================================

  if (
    status ===
    DRAFT_STATUS.SENT
  ) {

    return (
      <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.04] p-5">

        <div className="flex items-center gap-2">

          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white text-xs text-black">
            ✓
          </span>

          <span className="text-xs font-semibold uppercase tracking-[0.14em] text-white/80">
            Sent
          </span>

        </div>


        <p className="mt-4 text-sm leading-6 text-white/70">
          Email successfully sent.
        </p>


        {draft.sent_at && (
          <p className="mt-2 text-[11px] text-white/30">
            {new Date(
              draft.sent_at
            ).toLocaleString()}
          </p>
        )}

      </div>
    );
  }


  // ============================================================
  // REJECTED
  // ============================================================

  if (
    status ===
    DRAFT_STATUS.REJECTED
  ) {

    return (
      <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.04] p-5">

        <div className="flex items-center gap-2">

          <span className="text-xs font-semibold uppercase tracking-[0.14em] text-white/60">
            Rejected
          </span>

        </div>


        <div className="mt-4 whitespace-pre-wrap text-sm leading-6 text-white/60">
          {draft.content}
        </div>

      </div>
    );
  }


  // ============================================================
  // MAIN DRAFT CARD
  // ============================================================

  const isApproved =
    status === DRAFT_STATUS.APPROVED;


  const isSavedToGmail =
    Boolean(
      draft.gmail_draft_id
    );


  // ============================================================
  // Confirmation helpers
  // ============================================================

  const recipient =
    draft.recipient ??
    draft.to ??
    draft.recipient_email ??
    draft.to_email ??
    "Google Team";


  const subject =
    draft.subject ??
    draft.email_subject ??
    "Re: Meeting";


  async function handleConfirmSend() {

    if (isLoading) {
      return;
    }


    const result =
      await onSend?.();


    /*
     * Close modal only after the request has been
     * successfully accepted.
     */
    if (result !== null) {
      setShowSendConfirmation(
        false
      );
    }

  }


  function handleCancelSend() {

    if (isSending) {
      return;
    }


    setShowSendConfirmation(
      false
    );
  }


  return (
    <>

      <div className="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04]">

        {/* HEADER */}

        <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">

          <div className="flex items-center gap-2">

            {isApproved ? (
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white text-[10px] text-black">
                ✓
              </span>
            ) : (
              <span className="h-2 w-2 rounded-full bg-white/50" />
            )}

            <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/70">
              {isApproved
                ? "Approved"
                : "Draft"}
            </span>

          </div>


          <span className="text-[10px] text-white/30">
            #{draft.draft_id}
          </span>

        </div>


        {/* APPROVAL / GMAIL STATUS */}

        {isApproved && (
          <div className="border-b border-white/10 px-4 py-3">

            <div className="flex flex-wrap gap-3">

              <span className="text-xs text-white/70">
                ✓ Draft approved
              </span>


              {isSavedToGmail && (
                <span className="text-xs text-white/70">
                  ✓ Saved to Gmail
                </span>
              )}

            </div>

          </div>
        )}


        {/* CONTENT */}

        <div className="px-4 py-5">

          <div className="whitespace-pre-wrap text-sm leading-7 text-white/80">
            {draft.content ||
              "No draft content."}
          </div>

        </div>


        {/* META */}

        {(draft.version ||
          draft.tone) && (
          <div className="flex gap-3 px-4 pb-3 text-[10px] text-white/30">

            {draft.version && (
              <span>
                Version {draft.version}
              </span>
            )}

            {draft.tone && (
              <span>
                {draft.tone}
              </span>
            )}

          </div>
        )}


        {/* ACTIONS */}

        <div className="flex flex-wrap gap-2 border-t border-white/10 px-4 py-3">

          {/* EDIT */}

          <button
            type="button"
            disabled={isLoading}
            onClick={() =>
              setIsEditing(true)
            }
            className="rounded-lg border border-white/10 px-3 py-2 text-xs text-white/60 transition hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            Edit
          </button>


          {/* PENDING */}

          {!isApproved && (
            <>

              <button
                type="button"
                disabled={isLoading}
                onClick={() =>
                  onRegenerate?.()
                }
                className="rounded-lg border border-white/10 px-3 py-2 text-xs text-white/60 transition hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
              >
                {isRegenerating
                  ? "Generating..."
                  : "Regenerate"}
              </button>


              <button
                type="button"
                disabled={isLoading}
                onClick={() =>
                  onApprove?.()
                }
                className="rounded-lg bg-white px-3 py-2 text-xs font-medium text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {isApproving
                  ? "Approving..."
                  : "Approve"}
              </button>


              {onReject && (
                <button
                  type="button"
                  disabled={isLoading}
                  onClick={() =>
                    onReject?.()
                  }
                  className="rounded-lg border border-white/10 px-3 py-2 text-xs text-white/50 transition hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {isRejecting
                    ? "Rejecting..."
                    : "Reject"}
                </button>
              )}

            </>
          )}


          {/* APPROVED → SAVE TO GMAIL */}

          {isApproved &&
            !isSavedToGmail && (
              <button
                type="button"
                disabled={
                  isLoading ||
                  !onSaveToGmail
                }
                onClick={() =>
                  onSaveToGmail?.()
                }
                className="rounded-lg bg-white px-3 py-2 text-xs font-medium text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {isSavingToGmail
                  ? "Saving..."
                  : "Save to Gmail"}
              </button>
            )}


          {/* SAVED TO GMAIL → SEND */}

          {isApproved &&
            isSavedToGmail && (
              <button
                type="button"
                disabled={isLoading}
                onClick={() =>
                  setShowSendConfirmation(
                    true
                  )
                }
                className="rounded-lg bg-white px-3 py-2 text-xs font-medium text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Send
              </button>
            )}

        </div>

      </div>


      {/* SEND CONFIRMATION MODAL */}

      {showSendConfirmation && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 px-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="send-confirmation-title"
        >

          <div className="w-full max-w-lg overflow-hidden rounded-2xl border border-white/10 bg-neutral-950 shadow-2xl">

            {/* HEADER */}

            <div className="border-b border-white/10 px-5 py-4">

              <h2
                id="send-confirmation-title"
                className="text-base font-semibold text-white"
              >
                Send this email?
              </h2>

              <p className="mt-1 text-xs text-white/40">
                Please review the email before sending.
              </p>

            </div>


            {/* EMAIL PREVIEW */}

            <div className="px-5 py-5">

              <div className="space-y-3">

                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-white/35">
                    To
                  </p>

                  <p className="mt-1 text-sm text-white/80">
                    {recipient}
                  </p>
                </div>


                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-white/35">
                    Subject
                  </p>

                  <p className="mt-1 text-sm text-white/80">
                    {subject}
                  </p>
                </div>


                <div className="border-t border-white/10 pt-4">

                  <div className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm leading-6 text-white/70">
                    {draft.content ||
                      "No email content."}
                  </div>

                </div>

              </div>

            </div>


            {/* MODAL ACTIONS */}

            <div className="flex justify-end gap-2 border-t border-white/10 px-5 py-4">

              <button
                type="button"
                disabled={isSending}
                onClick={
                  handleCancelSend
                }
                className="rounded-lg border border-white/10 px-4 py-2 text-xs font-medium text-white/60 transition hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
              >
                Cancel
              </button>


              <button
                type="button"
                disabled={isSending}
                onClick={
                  handleConfirmSend
                }
                className="flex min-w-[80px] items-center justify-center gap-2 rounded-lg bg-white px-4 py-2 text-xs font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
              >

                {isSending ? (
                  <>
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-black/25 border-t-black" />
                    Sending...
                  </>
                ) : (
                  "Send"
                )}

              </button>

            </div>

          </div>

        </div>
      )}

    </>
  );
}