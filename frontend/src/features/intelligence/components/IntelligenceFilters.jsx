"use client";

const filters = [
  {
    value: "all",
    label: "All",
  },
  {
    value: "urgent",
    label: "Urgent",
  },
  {
    value: "reply_required",
    label: "Action required",
  },
  {
    value: "meeting",
    label: "Meetings",
  },
  {
    value: "deadline",
    label: "Deadlines",
  },
  {
    value: "finance",
    label: "Finance",
  },
  {
    value: "internship",
    label: "Internships",
  },
];


export default function IntelligenceFilters({
  value,
  onChange,
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {filters.map((filter) => {
        const active =
          value === filter.value;

        return (
          <button
            key={filter.value}
            onClick={() =>
              onChange(filter.value)
            }
            className={`whitespace-nowrap rounded-full px-4 py-2 text-xs font-medium transition ${
              active
                ? "bg-black text-white"
                : "bg-black/5 text-black/50 hover:bg-black/10 hover:text-black"
            }`}
          >
            {filter.label}
          </button>
        );
      })}
    </div>
  );
}