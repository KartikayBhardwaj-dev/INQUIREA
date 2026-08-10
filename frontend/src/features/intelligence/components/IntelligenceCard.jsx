"use client";

import {
  getCategoryLabel,
  getPriorityLabel,
  requiresReply,
  getOrganizations,
} from "./intelligence-utils";


function formatDate(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  return new Intl.DateTimeFormat(
    "en",
    {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }
  ).format(date);
}


function priorityClass(priority) {
  if (priority === "urgent") {
    return "bg-black text-white";
  }

  if (priority === "high") {
    return "bg-black/10 text-black";
  }

  return "bg-black/5 text-black/50";
}


export default function IntelligenceCard({
  item,
  selected = false,
  compact = false,
  onClick,
}) {
  const organizations =
    getOrganizations(item);

  const reply = requiresReply(item);

  return (
    <button
      onClick={onClick}
      className={`w-full rounded-2xl border bg-white p-5 text-left transition ${
        selected
          ? "border-black/30 shadow-sm"
          : "border-black/8 hover:border-black/20 hover:shadow-sm"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wider ${priorityClass(
                item.priority
              )}`}
            >
              {getPriorityLabel(
                item.priority
              )}
            </span>

            <span className="rounded-full bg-black/5 px-2 py-1 text-[10px] font-medium text-black/45">
              {getCategoryLabel(
                item.category
              )}
            </span>
          </div>

          <h3 className="mt-3 truncate text-sm font-semibold">
            {item.subject || "Untitled email"}
          </h3>

          <p className="mt-1 truncate text-xs text-black/40">
            {item.sender}
          </p>
        </div>

        <span className="shrink-0 text-xs text-black/30">
          {formatDate(item.received_at)}
        </span>
      </div>

      <p
        className={`mt-4 text-sm leading-6 text-black/60 ${
          compact ? "line-clamp-2" : "line-clamp-3"
        }`}
      >
        {item.summary ||
          "INQUIREA has not generated a summary yet."}
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {reply && (
          <span className="rounded-full border border-black/10 px-2.5 py-1 text-xs font-medium">
            Reply required
          </span>
        )}

        {organizations
          .slice(0, 2)
          .map((organization) => (
            <span
              key={organization}
              className="text-xs text-black/35"
            >
              {organization}
            </span>
          ))}
      </div>
    </button>
  );
}