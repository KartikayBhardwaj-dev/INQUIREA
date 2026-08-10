"use client";


function formatDate(value) {
  if (!value) {
    return "Unknown";
  }

  try {
    return new Intl.DateTimeFormat(
      "en",
      {
        dateStyle: "medium",
      }
    ).format(
      new Date(value)
    );
  } catch {
    return "Unknown";
  }
}


function getPriorityClass(priority) {
  switch (
    String(
      priority ?? ""
    ).toLowerCase()
  ) {
    case "urgent":
      return "bg-red-500/10 text-red-600 dark:text-red-400";

    case "high":
      return "bg-orange-500/10 text-orange-600 dark:text-orange-400";

    case "medium":
      return "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400";

    default:
      return "bg-black/5 text-black/50 dark:bg-white/10 dark:text-white/50";
  }
}


export default function EmailCard({
  email,
  onOpen,
  onReply,
}) {
  if (!email) {
    return null;
  }

  return (
    <div className="group mt-3 overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] shadow-sm transition hover:-translate-y-0.5 hover:bg-white/[0.06] hover:shadow-md">
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="truncate text-xs font-medium text-white/45">
              {email.sender ||
                "Unknown sender"}
            </p>

            <h3 className="mt-1 line-clamp-2 text-sm font-semibold text-white">
              {email.subject ||
                "Untitled email"}
            </h3>
          </div>

          <span
            className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase ${getPriorityClass(
              email.priority
            )}`}
          >
            {email.priority ??
              "normal"}
          </span>
        </div>


        <div className="mt-3 flex flex-wrap items-center gap-2">
          {email.requires_reply && (
            <span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-semibold text-black">
              Reply required
            </span>
          )}

          {email.category && (
            <span className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] text-white/45">
              {String(
                email.category
              ).replaceAll(
                "_",
                " "
              )}
            </span>
          )}

          <span className="text-[10px] text-white/30">
            {formatDate(
              email.received_at
            )}
          </span>
        </div>


        {email.summary && (
          <p className="mt-3 line-clamp-3 text-xs leading-5 text-white/55">
            {email.summary}
          </p>
        )}
      </div>


      <div className="flex border-t border-white/10 bg-white/[0.02]">
        <button
          type="button"
          onClick={() =>
            onOpen?.(email)
          }
          className="flex-1 px-4 py-3 text-xs font-medium text-white/80 transition hover:bg-white/5"
        >
          Open
        </button>

        <div className="w-px bg-white/10" />

        <button
          type="button"
          onClick={() =>
            onReply?.(email)
          }
          className="flex-1 px-4 py-3 text-xs font-medium text-white/80 transition hover:bg-white/5"
        >
          Reply
        </button>
      </div>
    </div>
  );
}