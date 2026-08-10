"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  getEmailDetails,
} from "@/features/chat/services/chat.service";


function formatDate(value) {
  if (!value) {
    return "Unknown";
  }

  try {
    return new Intl.DateTimeFormat(
      "en",
      {
        dateStyle: "medium",
        timeStyle: "short",
      }
    ).format(
      new Date(value)
    );
  } catch {
    return "Unknown";
  }
}


export default function EmailDetailsDrawer({
  email,
  onClose,
  onReply,
}) {
  const [
    details,
    setDetails,
  ] = useState(email);

  const [
    isLoading,
    setIsLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState(null);


  useEffect(() => {
    let cancelled = false;

    console.log(
      "🔵 EmailDetailsDrawer useEffect triggered"
    );

    console.log(
      "🔵 Email received by drawer:",
      email
    );


    async function load() {
      console.log(
        "🔵 load() started"
      );


      if (!email) {
        console.error(
          "🔴 No email received by EmailDetailsDrawer"
        );

        return;
      }


      console.log(
        "🟢 Email received:",
        email
      );

      console.log(
        "🟢 Local email_id:",
        email.email_id
      );

      console.log(
        "🟢 Gmail message ID:",
        email.gmail_message_id
      );


      setDetails(email);
      setError(null);


      /*
       * IMPORTANT:
       *
       * email.email_id
       * = LOCAL database ID
       *
       * email.gmail_message_id
       * = ACTUAL Gmail message ID
       *
       * Gmail API requires gmail_message_id.
       */

      const gmailMessageId =
        email.gmail_message_id;


      console.log(
        "🟡 Gmail message ID extracted:",
        gmailMessageId
      );


      if (!gmailMessageId) {
        console.error(
          "🔴 Gmail message ID is missing!",
          email
        );

        setError(
          "This email does not have a Gmail message ID."
        );

        return;
      }


      setIsLoading(true);


      try {
        console.log(
          "🚀 ABOUT TO CALL getEmailDetails():",
          gmailMessageId
        );


        const data =
          await getEmailDetails(
            gmailMessageId
          );


        console.log(
          "✅ getEmailDetails() RESPONSE:",
          data
        );


        if (!cancelled) {
          setDetails(
            data?.email ??
            data
          );
        }
      } catch (err) {
        console.error(
          "❌ getEmailDetails() FAILED:",
          err
        );

        console.error(
          "❌ Gmail ID used:",
          gmailMessageId
        );


        if (!cancelled) {
          setError(
            "Unable to load the complete email."
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }


    load();


    return () => {
      cancelled = true;

      console.log(
        "🟣 EmailDetailsDrawer cleanup"
      );
    };
  }, [email]);


  if (!email) {
    return null;
  }


  return (
    <>
      {/* BACKDROP */}

      <div
        className="fixed inset-0 z-40 bg-black/50 backdrop-blur-[2px]"
        onClick={onClose}
      />


      {/* DRAWER */}

      <aside className="fixed inset-y-0 right-0 z-50 flex w-full max-w-xl flex-col border-l border-white/10 bg-neutral-950 text-white shadow-2xl">


        {/* HEADER */}

        <header className="flex shrink-0 items-center justify-between border-b border-white/10 px-5 py-4">

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/35">
              Email
            </p>

            <p className="mt-1 text-sm font-semibold text-white">
              Details
            </p>
          </div>


          <button
            type="button"
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 text-sm text-white/70 transition hover:bg-white/10 hover:text-white"
          >
            ×
          </button>

        </header>


        {/* CONTENT */}

        <div className="min-h-0 flex-1 overflow-y-auto p-6">


          {/* LOADING */}

          {isLoading && (
            <div className="mb-5 rounded-xl bg-white/5 px-4 py-3 text-xs text-white/40">
              Loading email...
            </div>
          )}


          {/* ERROR */}

          {error && (
            <div className="mb-5 rounded-xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-xs text-red-300">
              {error}
            </div>
          )}


          {/* BADGES */}

          <div className="flex flex-wrap gap-2">

            {details?.priority && (
              <span className="rounded-full bg-white px-3 py-1.5 text-[10px] font-semibold uppercase text-black">
                {details.priority}
              </span>
            )}


            {details?.category && (
              <span className="rounded-full bg-white/10 px-3 py-1.5 text-[10px] font-medium text-white/60">
                {String(
                  details.category
                ).replaceAll(
                  "_",
                  " "
                )}
              </span>
            )}


            {(details?.requires_reply ||
              details?.reply_required) && (
              <span className="rounded-full border border-white/10 px-3 py-1.5 text-[10px] font-medium text-white/70">
                Reply required
              </span>
            )}

          </div>


          {/* SUBJECT */}

          <h1 className="mt-6 text-2xl font-semibold leading-tight tracking-tight text-white">
            {details?.subject ??
              "Untitled email"}
          </h1>


          {/* SENDER */}

          <div className="mt-5">

            <p className="text-sm font-medium text-white">
              {details?.sender ??
                details?.from ??
                "Unknown sender"}
            </p>


            <p className="mt-1 text-xs text-white/35">
              {formatDate(
                details?.received_at ??
                details?.date
              )}
            </p>

          </div>


          <div className="my-7 border-t border-white/10" />


          {/* AI SUMMARY */}

          {details?.summary && (
            <section className="mb-8">

              <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/35">
                AI Summary
              </p>


              <p className="mt-3 text-sm leading-7 text-white/65">
                {details.summary}
              </p>

            </section>
          )}


          {/* EMAIL BODY */}

          <section>

            <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/35">
              Email body
            </p>


            <div className="mt-3 whitespace-pre-wrap rounded-2xl bg-white/[0.04] p-5 text-sm leading-7 text-white/70">

              {details?.body ??
                details?.content ??
                details?.text ??
                details?.snippet ??
                "No email body available."}

            </div>

          </section>


          {/* TAGS */}

          {details?.tags?.length > 0 && (
            <section className="mt-8">

              <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/35">
                Tags
              </p>


              <div className="mt-3 flex flex-wrap gap-2">

                {details.tags.map(
                  (tag, index) => (
                    <span
                      key={`${tag}-${index}`}
                      className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-white/70"
                    >
                      {tag}
                    </span>
                  )
                )}

              </div>

            </section>
          )}

        </div>


        {/* FOOTER */}

        <footer className="shrink-0 border-t border-white/10 bg-neutral-950 p-4">

          <button
            type="button"
            onClick={() =>
              onReply?.(details)
            }
            className="w-full rounded-xl bg-white px-4 py-3 text-xs font-semibold text-black transition hover:bg-white/90"
          >
            Generate Reply
          </button>

        </footer>

      </aside>
    </>
  );
}