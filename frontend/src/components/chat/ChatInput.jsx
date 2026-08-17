"use client";

import {
  useState,
} from "react";


export default function ChatInput({
  onSend,
  disabled = false,
  isLoading = false,
}) {

  const [
    value,
    setValue,
  ] = useState("");


  const isSending =
    disabled ||
    isLoading;


  function submit() {

    const message =
      value.trim();


    if (
      !message ||
      isSending
    ) {
      return;
    }


    /*
     * Clear immediately.
     *
     * This also prevents the same message from being
     * accidentally submitted again through the UI.
     */
    setValue("");


    onSend?.(message);
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
            disabled={isSending}
            rows={1}
            placeholder={
              isSending
                ? "Sending..."
                : "Ask anything about your emails..."
            }
            className="min-h-[58px] w-full resize-none bg-transparent px-4 py-4 pr-20 text-sm leading-6 text-white outline-none placeholder:text-white/35 disabled:cursor-not-allowed disabled:opacity-60"
          />


          <button
            type="button"
            onClick={submit}
            disabled={
              isSending ||
              !value.trim()
            }
            className="absolute bottom-2.5 right-2.5 flex h-10 min-w-10 items-center justify-center gap-1.5 rounded-xl bg-white px-3 text-sm font-bold text-black transition hover:scale-105 hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-30"
            aria-label="Send message"
          >

            {isSending ? (
              <>
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-black/25 border-t-black" />

                <span className="text-[10px] font-semibold">
                  Sending...
                </span>
              </>
            ) : (
              "↑"
            )}

          </button>

        </div>


        <p className="mt-2 text-center text-[10px] text-white/30">
          {isSending
            ? "Sending your message..."
            : "Enter to send · Shift + Enter for a new line"}
        </p>

      </div>

    </div>
  );
}