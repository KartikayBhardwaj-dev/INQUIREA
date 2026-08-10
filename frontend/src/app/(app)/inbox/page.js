"use client";

import {
  useMemo,
  useState,
} from "react";

import IntelligenceCard from "@/features/intelligence/components/IntelligenceCard";
import IntelligenceFilters from "@/features/intelligence/components/IntelligenceFilters";
import SyncButton from "@/features/intelligence/components/SyncButton";

import {
  useEmailIntelligence,
} from "@/features/intelligence/hooks/useEmailIntelligence";

import {
  getCategoryLabel,
  getPriorityLabel,
  requiresReply,
  getActionItems,
  getOrganizations,
  getPeople,
} from "@/features/intelligence/components/intelligence-utils";

import ConversationSidebar from "@/components/chat/ConversationSidebar";
import ChatMessages from "@/components/chat/ChatMessages";
import ChatInput from "@/components/chat/ChatInput";
import EmailDetailsDrawer from "@/components/chat/EmailDetailsDrawer";

import useChat from "@/features/chat/hooks/useChat";


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
    ).format(new Date(value));
  } catch {
    return "Unknown";
  }
}


export default function InboxPage() {
  /*
   * ----------------------------------------------------------------------
   * EMAIL INTELLIGENCE
   * ----------------------------------------------------------------------
   */

  const {
    data = [],
    isLoading,
    isError,
  } = useEmailIntelligence();


  const [
    filter,
    setFilter,
  ] = useState("all");


  const [
    selectedId,
    setSelectedId,
  ] = useState(null);


  /*
   * ----------------------------------------------------------------------
   * AI CHAT
   * ----------------------------------------------------------------------
   */

  const {
    messages,
    conversations,
    activeConversationId,

    isLoading: isChatLoading,
    isLoadingConversations,

    error: chatError,

    sendMessage,
    loadConversation,
    newConversation,
    regenerate,
  } = useChat();


  /*
   * ----------------------------------------------------------------------
   * AI FULL PAGE
   * ----------------------------------------------------------------------
   */

  const [
    isChatOpen,
    setIsChatOpen,
  ] = useState(false);


  /*
   * ----------------------------------------------------------------------
   * EMAIL DETAILS
   * ----------------------------------------------------------------------
   */

  const [
    selectedEmail,
    setSelectedEmail,
  ] = useState(null);


  /*
   * ----------------------------------------------------------------------
   * FILTER INTELLIGENCE
   * ----------------------------------------------------------------------
   */

  const filteredData = useMemo(() => {
    if (filter === "all") {
      return data;
    }

    if (filter === "urgent") {
      return data.filter(
        (item) =>
          item.priority === "urgent" ||
          item.priority === "high"
      );
    }

    if (filter === "reply_required") {
      return data.filter(
        (item) =>
          requiresReply(item) ||
          item.category === "reply_required"
      );
    }

    return data.filter(
      (item) =>
        item.category === filter
    );
  }, [
    data,
    filter,
  ]);


  /*
   * ----------------------------------------------------------------------
   * SELECTED EMAIL INTELLIGENCE
   * ----------------------------------------------------------------------
   */

  const selected =
    filteredData.find(
      (item) =>
        item.id === selectedId
    ) ||
    filteredData[0] ||
    null;


  /*
   * ----------------------------------------------------------------------
   * CHAT REPLY
   * ----------------------------------------------------------------------
   */

  function handleReply(email) {
    if (!email) {
      return;
    }

    const subject =
      email.subject ??
      "this email";

    setSelectedEmail(null);

    setIsChatOpen(true);

    sendMessage(
      `Generate a reply to the email "${subject}".`
    );
  }


  /*
   * ----------------------------------------------------------------------
   * LOADING
   * ----------------------------------------------------------------------
   */

  if (isLoading) {
    return (
      <div className="py-20 text-center text-sm text-black/40">
        Understanding your inbox...
      </div>
    );
  }


  /*
   * ----------------------------------------------------------------------
   * ERROR
   * ----------------------------------------------------------------------
   */

  if (isError) {
    return (
      <div className="rounded-2xl border border-black/8 bg-white p-8">
        <p className="font-medium">
          Unable to load AI Inbox.
        </p>

        <p className="mt-1 text-sm text-black/40">
          Please try again.
        </p>
      </div>
    );
  }


  /*
   * ----------------------------------------------------------------------
   * FULL SCREEN AI CHAT
   * ----------------------------------------------------------------------
   */

  if (isChatOpen) {
    return (
      <div className="fixed inset-0 z-[100] flex h-[100dvh] w-screen overflow-hidden bg-black text-white">
        {/* --------------------------------------------------------------
            CONVERSATION SIDEBAR
        -------------------------------------------------------------- */}

        <aside className="hidden h-full w-[280px] shrink-0 border-r border-white/10 bg-black lg:block">
          <ConversationSidebar
            conversations={
              conversations
            }
            activeConversationId={
              activeConversationId
            }
            onSelect={
              loadConversation
            }
            onNewConversation={
              newConversation
            }
            isLoading={
              isLoadingConversations
            }
          />
        </aside>


        {/* --------------------------------------------------------------
            CHAT AREA
        -------------------------------------------------------------- */}

        <main className="flex min-w-0 flex-1 flex-col bg-black text-white">
          {/* Header */}

          <header className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 bg-black px-5">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-sm font-bold text-black">
                ✦
              </div>

              <div>
                <h1 className="text-sm font-semibold text-white">
                  AI Inbox
                </h1>

                <p className="text-[11px] text-white/40">
                  Ask anything about your emails
                </p>
              </div>
            </div>


            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={
                  newConversation
                }
                className="rounded-xl border border-white/10 px-3 py-2 text-xs font-medium text-white transition hover:bg-white/10"
              >
                New Chat
              </button>


              <button
                type="button"
                onClick={() =>
                  setIsChatOpen(false)
                }
                className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 text-lg text-white/70 transition hover:bg-white/10 hover:text-white"
                aria-label="Close AI"
              >
                ×
              </button>
            </div>
          </header>


          {/* Error */}

          {chatError && (
            <div className="border-b border-red-400/20 bg-red-500/10 px-5 py-2 text-center text-xs text-red-300">
              {chatError}
            </div>
          )}


          {/* Messages */}

          <ChatMessages
            messages={messages}
            isLoading={
              isChatLoading
            }
            onSuggestion={
              sendMessage
            }
            onOpenEmail={
              setSelectedEmail
            }
            onReplyEmail={
              handleReply
            }
            onRegenerate={
              regenerate
            }
          />


          {/* Input */}

          <ChatInput
            onSend={
              sendMessage
            }
            disabled={
              isChatLoading
            }
          />
        </main>


        {/* Email details */}

        <EmailDetailsDrawer
          email={
            selectedEmail
          }
          onClose={() =>
            setSelectedEmail(
              null
            )
          }
          onReply={
            handleReply
          }
        />
      </div>
    );
  }


  /*
   * ----------------------------------------------------------------------
   * NORMAL AI INBOX PAGE
   * ----------------------------------------------------------------------
   */

  return (
    <div className="space-y-7">
      {/* Header */}

      <header className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-black/35">
            INQUIREA
          </p>

          <h1 className="mt-2 text-4xl font-semibold tracking-tight">
            AI Inbox
          </h1>

          <p className="mt-2 text-sm text-black/45">
            Your emails, understood instead of merely displayed.
          </p>
        </div>


        <div className="flex items-center gap-2">
          <SyncButton />


          <button
            type="button"
            onClick={() =>
              setIsChatOpen(true)
            }
            className="inline-flex items-center gap-2 rounded-xl bg-black px-4 py-2.5 text-sm font-medium text-white transition hover:bg-black/80"
          >
            <span>
              ✦
            </span>

            <span>
              Ask AI
            </span>
          </button>
        </div>
      </header>


      {/* Stats */}

      <div className="flex flex-wrap gap-5 text-sm text-black/45">
        <span>
          <strong className="text-black">
            {data.length}
          </strong>{" "}
          understood
        </span>

        <span>
          <strong className="text-black">
            {
              data.filter(
                (item) =>
                  item.priority ===
                  "urgent"
              ).length
            }
          </strong>{" "}
          urgent
        </span>

        <span>
          <strong className="text-black">
            {
              data.filter(
                (item) =>
                  requiresReply(item)
              ).length
            }
          </strong>{" "}
          need action
        </span>
      </div>


      {/* Filters */}

      <IntelligenceFilters
        value={filter}
        onChange={setFilter}
      />


      {/* Empty */}

      {filteredData.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-black/10 bg-white p-16 text-center">
          <div className="text-2xl">
            ✦
          </div>

          <p className="mt-3 font-medium">
            Nothing here yet.
          </p>

          <p className="mt-1 text-sm text-black/40">
            Try another intelligence filter.
          </p>
        </div>
      ) : (
        <div className="grid min-h-[650px] overflow-hidden rounded-3xl border border-black/8 bg-white lg:grid-cols-[minmax(0,1fr)_420px]">
          {/* List */}

          <div className="border-r border-black/8">
            <div className="border-b border-black/8 px-5 py-4">
              <span className="text-xs font-semibold uppercase tracking-[0.14em] text-black/35">
                Intelligence feed
              </span>
            </div>


            <div className="divide-y divide-black/5">
              {filteredData.map(
                (item) => (
                  <div
                    key={item.id}
                    className="p-3"
                  >
                    <IntelligenceCard
                      item={item}
                      selected={
                        selected?.id ===
                        item.id
                      }
                      onClick={() =>
                        setSelectedId(
                          item.id
                        )
                      }
                    />
                  </div>
                )
              )}
            </div>
          </div>


          {/* Detail */}

          <IntelligenceDetail
            item={selected}
          />
        </div>
      )}
    </div>
  );
}


/* =========================================================================
   INTELLIGENCE DETAIL
========================================================================= */

function IntelligenceDetail({
  item,
}) {
  if (!item) {
    return (
      <div className="flex items-center justify-center p-10 text-center">
        <div>
          <div className="text-3xl">
            ✦
          </div>

          <p className="mt-3 text-sm font-medium">
            Select an insight
          </p>

          <p className="mt-1 text-xs text-black/40">
            Choose an email from the intelligence feed.
          </p>
        </div>
      </div>
    );
  }


  const actionItems =
    getActionItems(item);

  const organizations =
    getOrganizations(item);

  const people =
    getPeople(item);


  return (
    <div className="overflow-y-auto p-7">
      <div className="flex flex-wrap gap-2">
        <span className="rounded-full bg-black px-3 py-1.5 text-xs font-semibold text-white">
          {getPriorityLabel(
            item.priority
          )}
        </span>

        <span className="rounded-full bg-black/5 px-3 py-1.5 text-xs font-medium text-black/50">
          {getCategoryLabel(
            item.category
          )}
        </span>

        {requiresReply(item) && (
          <span className="rounded-full border border-black/10 px-3 py-1.5 text-xs font-medium">
            Reply required
          </span>
        )}
      </div>


      <h2 className="mt-6 text-2xl font-semibold leading-tight tracking-tight">
        {item.subject ||
          "Untitled email"}
      </h2>


      <div className="mt-4">
        <p className="text-sm font-medium">
          {item.sender}
        </p>

        <p className="mt-1 text-xs text-black/35">
          {formatDate(
            item.received_at
          )}
        </p>
      </div>


      <div className="my-7 border-t border-black/8" />


      <section>
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-black/35">
          AI Summary
        </p>

        <p className="mt-3 text-sm leading-7 text-black/65">
          {item.summary ||
            "No summary available."}
        </p>
      </section>


      {actionItems.length > 0 && (
        <section className="mt-8">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-black/35">
            Suggested actions
          </p>

          <div className="mt-3 space-y-2">
            {actionItems.map(
              (
                action,
                index
              ) => (
                <div
                  key={`${action}-${index}`}
                  className="rounded-xl bg-black/5 p-3 text-sm"
                >
                  {action}
                </div>
              )
            )}
          </div>
        </section>
      )}


      {organizations.length > 0 && (
        <section className="mt-8">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-black/35">
            Organizations
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            {organizations.map(
              (organization) => (
                <span
                  key={organization}
                  className="rounded-full border border-black/10 px-3 py-1.5 text-xs"
                >
                  {organization}
                </span>
              )
            )}
          </div>
        </section>
      )}


      {people.length > 0 && (
        <section className="mt-8">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-black/35">
            People
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            {people.map(
              (person) => (
                <span
                  key={person}
                  className="rounded-full border border-black/10 px-3 py-1.5 text-xs"
                >
                  {person}
                </span>
              )
            )}
          </div>
        </section>
      )}
    </div>
  );
}