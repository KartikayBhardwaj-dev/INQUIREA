"use client";

import {
  useEffect,
  useRef,
} from "react";

import ChatMessage from "./ChatMessage";


const suggestions = [
  "Find emails requiring a reply.",
  "Show me important emails from this week.",
  "Find emails related to internships.",
  "What did Amazon send me?",
];


export default function ChatMessages({
  messages = [],
  isLoading,
  onSuggestion,
  onOpenEmail,
  onReplyEmail,
  onRegenerate,
}) {
  const bottomRef =
    useRef(null);


  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [
    messages,
    isLoading,
  ]);


  return (
    <div className="min-h-0 flex-1 overflow-y-auto bg-black text-white">
      {messages.length === 0 ? (
        <EmptyChat
          onSuggestion={
            onSuggestion
          }
        />
      ) : (
        <div className="mx-auto max-w-5xl py-6">
          {messages.map(
            (
              message,
              index
            ) => (
              <ChatMessage
                key={
                  message.id ??
                  message.message_id ??
                  `${message.role}-${index}`
                }
                message={
                  message
                }
                messageIndex={
                  index
                }
                onOpenEmail={
                  onOpenEmail
                }
                onReplyEmail={
                  onReplyEmail
                }
                onRegenerate={
                  onRegenerate
                }
              />
            )
          )}


          {isLoading && (
            <ThinkingState />
          )}


          <div
            ref={bottomRef}
            className="h-4"
          />
        </div>
      )}
    </div>
  );
}


/* =========================================================================
   EMPTY CHAT
========================================================================= */

function EmptyChat({
  onSuggestion,
}) {
  return (
    <div className="flex min-h-full items-center justify-center px-6 py-16">
      <div className="w-full max-w-3xl text-center">
        {/* AI ICON */}

        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-xl font-bold text-black shadow-xl">
          ✦
        </div>


        <h2 className="mt-6 text-3xl font-semibold tracking-tight text-white">
          Ask anything about your inbox.
        </h2>


        <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-white/45">
          Search, understand, summarize and work
          with your emails using natural language.
        </p>


        {/* SUGGESTIONS */}

        <div className="mt-8 grid gap-3 sm:grid-cols-2">
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
                className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-4 text-left text-xs font-medium text-white/75 transition hover:-translate-y-0.5 hover:border-white/20 hover:bg-white/[0.08] hover:text-white"
              >
                {suggestion}
              </button>
            )
          )}
        </div>
      </div>
    </div>
  );
}


/* =========================================================================
   THINKING
========================================================================= */

function ThinkingState() {
  return (
    <div className="px-4 py-4 sm:px-8">
      <div className="mx-auto flex max-w-5xl items-center gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white text-xs font-bold text-black">
          ✦
        </div>


        <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.05] px-4 py-3">
          <span className="flex gap-1">
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white [animation-delay:-0.3s]" />

            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white [animation-delay:-0.15s]" />

            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white" />
          </span>


          <span className="text-xs text-white/45">
            Searching your emails...
          </span>
        </div>
      </div>
    </div>
  );
}