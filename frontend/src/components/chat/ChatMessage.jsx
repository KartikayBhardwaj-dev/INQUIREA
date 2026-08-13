"use client";

import { useState } from "react";

import MarkdownRenderer from "@/components/MarkdownRenderer";

import EmailCard from "./EmailCard";
import ChatActionRenderer from "./ChatActionRenderer";


export default function ChatMessage({
  message,
  onOpenEmail,
  onReplyEmail,
  onRegenerate,
}) {
  const isUser =
    message.role === "user";

  const [
    copied,
    setCopied,
  ] = useState(false);


  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(
        message.content ?? ""
      );

      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 1500);
    } catch {
      // Clipboard unavailable.
    }
  }


  /* ----------------------------------------------------------------------
     USER MESSAGE
  ---------------------------------------------------------------------- */

  if (isUser) {
    return (
      <div className="flex justify-end px-4 py-2 sm:px-8">
        <div className="max-w-[min(720px,85%)] rounded-2xl rounded-br-md bg-white px-4 py-3 text-sm leading-6 text-black shadow-lg">
          {message.content}
        </div>
      </div>
    );
  }


  /* ----------------------------------------------------------------------
     AI MESSAGE
  ---------------------------------------------------------------------- */

  return (
    <div className="px-4 py-4 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-start gap-3">

          {/* AI ICON */}

          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white text-xs font-bold text-black shadow-sm">
            ✦
          </div>


          <div className="min-w-0 flex-1">

            {/* ----------------------------------------------------------
                AI TEXT RESPONSE
                ---------------------------------------------------------- */}

            {message.content && (
              <div className="text-sm leading-7 text-white/80">
                <MarkdownRenderer>
                  {message.content}
                </MarkdownRenderer>
              </div>
            )}


            {/* ----------------------------------------------------------
                STRUCTURED ACTION
               
                Task 29:
                ChatMessage does NOT interpret:
                  - tool
                  - tool_result
                  - draft_id
                  - approval_status
                  - sent status

                useChat has already converted the backend
                response into message.action.

                ChatActionRenderer is responsible for
                rendering the correct action UI.
                ---------------------------------------------------------- */}

            {message.action && (
              <div className="mt-4">
                <ChatActionRenderer
                  action={message.action}
                />
              </div>
            )}


            {/* ----------------------------------------------------------
                RETRIEVED EMAILS
                ---------------------------------------------------------- */}

            {message.retrievedEmails?.length > 0 && (
              <div className="mt-5 space-y-3">

                <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/35">
                  Relevant emails
                </p>

                {message.retrievedEmails.map(
                  (email, index) => (
                    <EmailCard
                      key={
                        email.id ??
                        email.message_id ??
                        `${email.subject ?? "email"}-${index}`
                      }
                      email={email}
                      onOpen={onOpenEmail}
                      onReply={onReplyEmail}
                    />
                  )
                )}

              </div>
            )}


            {/* ----------------------------------------------------------
                MESSAGE ACTIONS
                ---------------------------------------------------------- */}

            <div className="mt-3 flex items-center gap-1">

              <button
                type="button"
                onClick={handleCopy}
                className="rounded-lg px-2 py-1 text-[10px] text-white/35 transition hover:bg-white/10 hover:text-white/80"
              >
                {copied
                  ? "Copied"
                  : "Copy"}
              </button>


              <button
                type="button"
                onClick={() =>
                  onRegenerate?.()
                }
                className="rounded-lg px-2 py-1 text-[10px] text-white/35 transition hover:bg-white/10 hover:text-white/80"
              >
                Regenerate
              </button>

            </div>

          </div>
        </div>
      </div>
    </div>
  );
}