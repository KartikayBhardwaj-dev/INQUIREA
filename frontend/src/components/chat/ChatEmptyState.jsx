"use client";


const suggestions = [
  "Find emails requiring a reply.",
  "Show me important emails from this week.",
  "Find my internship emails.",
  "Which emails are urgent?",
  "What did Amazon send me?",
  "Find my interview emails.",
];


export default function ChatEmptyState({
  onSuggestion,
}) {
  return (
    <div className="flex min-h-full flex-col items-center justify-center bg-black px-6 py-16 text-center text-white">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-xl font-bold text-black shadow-xl">
        AI
      </div>


      <h1 className="text-3xl font-semibold tracking-tight text-white">
        Ask anything about your inbox
      </h1>


      <p className="mt-3 max-w-lg text-sm leading-6 text-white/50">
        Search, understand, summarize and
        act on your emails using natural
        language.
      </p>


      <div className="mt-8 grid w-full max-w-2xl gap-3 sm:grid-cols-2">
        {suggestions.map(
          (suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() =>
                onSuggestion(
                  suggestion
                )
              }
              className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-left text-sm text-white/75 transition hover:border-white/20 hover:bg-white/[0.08] hover:text-white"
            >
              {suggestion}
            </button>
          )
        )}
      </div>
    </div>
  );
}