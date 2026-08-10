"use client";

import Link from "next/link";

import IntelligenceCard from "./IntelligenceCard";


export default function AttentionNeeded({
  data = [],
}) {
  const attention = data
    .filter((item) => {
      const reply =
        item?.extracted_data?.requires_reply;

      return (
        item.priority === "urgent" ||
        item.priority === "high" ||
        reply === true ||
        item.category === "reply_required"
      );
    })
    .slice(0, 4);

  return (
    <section>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-black/35">
            Attention
          </p>

          <h2 className="mt-1 text-xl font-semibold tracking-tight">
            What needs your attention
          </h2>
        </div>

        <Link
          href="/inbox"
          className="text-sm text-black/45 hover:text-black"
        >
          View AI Inbox →
        </Link>
      </div>

      {attention.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-black/10 bg-white p-8 text-center">
          <div className="text-2xl">✓</div>

          <p className="mt-3 font-medium">
            Nothing urgent right now
          </p>

          <p className="mt-1 text-sm text-black/40">
            Your inbox is under control.
          </p>
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {attention.map((item) => (
            <IntelligenceCard
              key={item.id}
              item={item}
              compact
            />
          ))}
        </div>
      )}
    </section>
  );
}