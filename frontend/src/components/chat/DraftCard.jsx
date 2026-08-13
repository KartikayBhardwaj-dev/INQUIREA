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
  onSend,
  isLoading = false,
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
          className="w-full resize-y rounded-xl border border-white/10 bg-black/20 p-3 text-sm leading-6 text-white outline-none transition focus:border-white/25"
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

              await onEdit?.(content);

              setIsEditing(false);
            }}
            className="rounded-lg bg-white px-3 py-2 text-xs font-medium text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isLoading
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
            className="rounded-lg border border-white/10 px-3 py-2 text-xs text-white/60 transition hover:bg-white/10 hover:text-white disabled:opacity-40"
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

  if (status === DRAFT_STATUS.SENT) {

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

  if (status === DRAFT_STATUS.REJECTED) {

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


  return (
    <div className="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04]">

      {/* ------------------------------------------------------
          HEADER
      ------------------------------------------------------ */}

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


      {/* ------------------------------------------------------
          CONTENT
      ------------------------------------------------------ */}

      <div className="px-4 py-5">

        <div className="whitespace-pre-wrap text-sm leading-7 text-white/80">
          {draft.content || "No draft content."}
        </div>

      </div>


      {/* ------------------------------------------------------
          META
      ------------------------------------------------------ */}

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


      {/* ------------------------------------------------------
          ACTIONS
      ------------------------------------------------------ */}

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
              Regenerate
            </button>


            <button
              type="button"
              disabled={isLoading}
              onClick={() =>
                onApprove?.()
              }
              className="rounded-lg bg-white px-3 py-2 text-xs font-medium text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Approve
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
                Reject
              </button>
            )}
          </>
        )}


        {/* APPROVED */}

        {isApproved && (
          <button
            type="button"
            disabled={isLoading}
            onClick={() =>
              onSend?.()
            }
            className="rounded-lg bg-white px-3 py-2 text-xs font-medium text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Send
          </button>
        )}

      </div>

    </div>
  );
}