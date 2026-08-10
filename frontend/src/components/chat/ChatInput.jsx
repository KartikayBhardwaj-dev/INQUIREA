"use client";

import {
  useState,
} from "react";


export default function ChatInput({
  onSend,
  disabled,
}) {
  const [
    value,
    setValue,
  ] = useState("");


  function submit() {
    const message =
      value.trim();

    if (
      !message ||
      disabled
    ) {
      return;
    }

    onSend(message);

    setValue("");
  }


  function handleKeyDown(
    event
  ) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      submit();
    }
  }


  return (
    <div className="shrink-0 border-t border-white/10 bg-black px-4 py-4 sm:px-8">
      <div className="mx-auto w-full max-w-4xl">
        <div className="relative rounded-2xl border border-white/15 bg-white/[0.06] shadow-lg transition focus-within:border-white/30 focus-within:bg-white/[0.08]">
          <textarea
            value={value}
            onChange={(event) =>
              setValue(
                event.target.value
              )
            }
            onKeyDown={
              handleKeyDown
            }
            disabled={disabled}
            rows={1}
            placeholder="Ask anything about your emails..."
            className="min-h-[58px] w-full resize-none bg-transparent px-4 py-4 pr-16 text-sm leading-6 text-white outline-none placeholder:text-white/35 disabled:cursor-not-allowed"
          />


          <button
            type="button"
            onClick={submit}
            disabled={
              disabled ||
              !value.trim()
            }
            className="absolute bottom-2.5 right-2.5 flex h-10 w-10 items-center justify-center rounded-xl bg-white text-sm font-bold text-black transition hover:scale-105 hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-20"
            aria-label="Send message"
          >
            ↑
          </button>
        </div>


        <p className="mt-2 text-center text-[10px] text-white/30">
          Enter to send · Shift + Enter for a new line
        </p>
      </div>
    </div>
  );
}