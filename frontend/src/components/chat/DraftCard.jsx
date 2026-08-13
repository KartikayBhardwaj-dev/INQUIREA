"use client";

import {
  DRAFT_STATUS,
} from "../../features/chat/models/draftState";


function getStatusLabel(draft) {
  if (draft?.is_sent) {
    return "SENT";
  }

  switch (draft?.approval_status) {
    case DRAFT_STATUS.APPROVED:
      return "APPROVED";

    case DRAFT_STATUS.REJECTED:
      return "REJECTED";

    case DRAFT_STATUS.PENDING:
    default:
      return "DRAFT";
  }
}


function getStatusIcon(draft) {
  if (draft?.is_sent) {
    return "✓";
  }

  switch (draft?.approval_status) {
    case DRAFT_STATUS.APPROVED:
      return "✓";

    case DRAFT_STATUS.REJECTED:
      return "×";

    case DRAFT_STATUS.PENDING:
    default:
      return null;
  }
}


export default function DraftCard({
  draft,
  onEdit,
  onRegenerate,
  onApprove,
  onSend,
}) {
  if (!draft) {
    return null;
  }


  const {
    draft_id,
    email_id,
    content,
    version,
    tone,
    approval_status,
    gmail_draft_id,
    is_sent,
    sent_at,
  } = draft;


  const status =
    is_sent
      ? DRAFT_STATUS.SENT
      : approval_status;


  const isPending =
    status === DRAFT_STATUS.PENDING;

  const isApproved =
    status === DRAFT_STATUS.APPROVED;

  const isRejected =
    status === DRAFT_STATUS.REJECTED;

  const isSent =
    is_sent ||
    status === DRAFT_STATUS.SENT;


  const statusLabel =
    getStatusLabel(draft);

  const statusIcon =
    getStatusIcon(draft);


  return (
    <div
      className="
        mt-4
        w-full
        max-w-2xl
        overflow-hidden
        rounded-2xl
        border
        border-white/10
        bg-white/[0.04]
        shadow-lg
      "
    >

      {/* ================================================================
          HEADER
          ================================================================ */}

      <div
        className="
          flex
          items-center
          justify-between
          border-b
          border-white/10
          px-4
          py-3
        "
      >

        <div className="flex items-center gap-2">

          {statusIcon && (
            <span
              className="
                flex
                h-5
                w-5
                items-center
                justify-center
                rounded-full
                bg-white/10
                text-xs
                font-semibold
              "
            >
              {statusIcon}
            </span>
          )}

          <span
            className="
              text-[11px]
              font-semibold
              uppercase
              tracking-[0.15em]
              text-white/70
            "
          >
            {statusLabel}
          </span>

        </div>


        {draft_id != null && (
          <span
            className="
              text-[10px]
              text-white/35
            "
          >
            Draft #{draft_id}
          </span>
        )}

      </div>


      {/* ================================================================
          CONTENT
          ================================================================ */}

      {!isSent ? (
        <div
          className="
            whitespace-pre-wrap
            px-4
            py-4
            text-sm
            leading-6
            text-white/80
          "
        >
          {content || "No draft content available."}
        </div>
      ) : (
        <div
          className="
            px-4
            py-5
            text-sm
            text-white/70
          "
        >
          Email successfully sent.
        </div>
      )}


      {/* ================================================================
          METADATA
          ================================================================ */}

      {!isSent && (
        <div
          className="
            flex
            flex-wrap
            gap-x-4
            gap-y-1
            px-4
            pb-3
            text-[10px]
            text-white/35
          "
        >

          {email_id != null && (
            <span>
              Email #{email_id}
            </span>
          )}

          {version != null && (
            <span>
              Version {version}
            </span>
          )}

          {tone && (
            <span>
              Tone: {tone}
            </span>
          )}

          {gmail_draft_id && (
            <span>
              Gmail draft
            </span>
          )}

        </div>
      )}


      {/* ================================================================
          PENDING
          ================================================================ */}

      {isPending && (
        <div
          className="
            flex
            flex-wrap
            gap-2
            border-t
            border-white/10
            px-4
            py-3
          "
        >

          <button
            type="button"
            onClick={() =>
              onEdit?.(draft)
            }
            className="
              rounded-lg
              border
              border-white/10
              px-3
              py-1.5
              text-xs
              text-white/70
              transition
              hover:bg-white/10
              hover:text-white
            "
          >
            Edit
          </button>


          <button
            type="button"
            onClick={() =>
              onRegenerate?.(draft)
            }
            className="
              rounded-lg
              border
              border-white/10
              px-3
              py-1.5
              text-xs
              text-white/70
              transition
              hover:bg-white/10
              hover:text-white
            "
          >
            Regenerate
          </button>


          <button
            type="button"
            onClick={() =>
              onApprove?.(draft)
            }
            className="
              rounded-lg
              bg-white
              px-3
              py-1.5
              text-xs
              font-medium
              text-black
              transition
              hover:bg-white/90
            "
          >
            Approve
          </button>

        </div>
      )}


      {/* ================================================================
          APPROVED
          ================================================================ */}

      {isApproved && (
        <div
          className="
            flex
            flex-wrap
            gap-2
            border-t
            border-white/10
            px-4
            py-3
          "
        >

          <button
            type="button"
            onClick={() =>
              onEdit?.(draft)
            }
            className="
              rounded-lg
              border
              border-white/10
              px-3
              py-1.5
              text-xs
              text-white/70
              transition
              hover:bg-white/10
              hover:text-white
            "
          >
            Edit
          </button>


          <button
            type="button"
            onClick={() =>
              onSend?.(draft)
            }
            className="
              rounded-lg
              bg-white
              px-3
              py-1.5
              text-xs
              font-medium
              text-black
              transition
              hover:bg-white/90
            "
          >
            Send
          </button>

        </div>
      )}


      {/* ================================================================
          REJECTED
          ================================================================ */}

      {isRejected && (
        <div
          className="
            border-t
            border-white/10
            px-4
            py-3
            text-xs
            text-white/45
          "
        >
          This draft was rejected.
        </div>
      )}


      {/* ================================================================
          SENT
          ================================================================ */}

      {isSent && (
        <div
          className="
            border-t
            border-white/10
            px-4
            py-3
            text-xs
            text-white/45
          "
        >
          {sent_at
            ? `Sent at ${sent_at}`
            : "Reply sent successfully."}
        </div>
      )}

    </div>
  );
}