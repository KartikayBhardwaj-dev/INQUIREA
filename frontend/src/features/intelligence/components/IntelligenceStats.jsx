"use client";

export default function IntelligenceStats({
  data = [],
}) {
  const urgent = data.filter(
    (item) => item.priority === "urgent"
  ).length;

  const high = data.filter(
    (item) => item.priority === "high"
  ).length;

  const actionRequired = data.filter(
    (item) =>
      item.extracted_data?.requires_reply === true ||
      item.category === "reply_required"
  ).length;

  const meetings = data.filter(
    (item) => item.category === "meeting"
  ).length;

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard
        label="Urgent"
        value={urgent}
        description="Needs attention"
      />

      <StatCard
        label="High priority"
        value={high}
        description="Important emails"
      />

      <StatCard
        label="Action required"
        value={actionRequired}
        description="Reply or action"
      />

      <StatCard
        label="Meetings"
        value={meetings}
        description="Detected by AI"
      />
    </div>
  );
}


function StatCard({
  label,
  value,
  description,
}) {
  return (
    <div className="rounded-2xl border border-black/8 bg-white p-5">
      <div className="text-sm text-black/50">
        {label}
      </div>

      <div className="mt-3 text-3xl font-semibold tracking-tight">
        {value}
      </div>

      <div className="mt-1 text-xs text-black/35">
        {description}
      </div>
    </div>
  );
}