"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import ConversationSidebar from "@/components/chat/ConversationSidebar";
import ChatMessages from "@/components/chat/ChatMessages";
import ChatInput from "@/components/chat/ChatInput";
import EmailDetailsDrawer from "@/components/chat/EmailDetailsDrawer";

import useChat from "@/features/chat/hooks/useChat";

export default function ConversationsPage() {
  const router = useRouter();

  const {
    messages,
    conversations,
    activeConversationId,

    isLoading,
    isLoadingConversations,

    error,

    sendMessage,
    loadConversation,
    newConversation,
    regenerate,
  } = useChat();

  const [selectedEmail, setSelectedEmail] =
    useState(null);

  function handleReply(email) {
    if (!email) {
      return;
    }

    const subject =
      email.subject ?? "this email";

    setSelectedEmail(null);

    sendMessage(
      `Generate a reply to the email "${subject}".`
    );
  }

  return (
    <div className="fixed inset-0 z-40 flex min-h-0 overflow-hidden bg-neutral-950 text-white">
      {/* =========================================================
          CONVERSATION SIDEBAR
      ========================================================= */}

      <aside className="hidden w-[270px] shrink-0 border-r border-white/10 bg-neutral-950 lg:flex lg:flex-col">
        {/* Sidebar Header */}

        <div className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 px-4">
          <button
            type="button"
            onClick={() => router.push("/inbox")}
            className="flex items-center gap-2 text-sm font-semibold text-white transition hover:text-white/70"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-white text-black">
              ✦
            </span>

            <span>INQUIREA</span>
          </button>
        </div>

        {/* Conversation history */}

        <div className="min-h-0 flex-1 overflow-hidden">
          <ConversationSidebar
            conversations={conversations}
            activeConversationId={
              activeConversationId
            }
            onSelect={loadConversation}
            onNewConversation={newConversation}
            isLoading={
              isLoadingConversations
            }
          />
        </div>
      </aside>

      {/* =========================================================
          MAIN CHAT
      ========================================================= */}

      <main className="flex min-w-0 flex-1 flex-col bg-neutral-950">
        {/* Header */}

        <header className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 bg-neutral-950 px-5">
          <div>
            <h1 className="text-sm font-semibold text-white">
              AI Inbox
            </h1>

            <p className="mt-0.5 text-[11px] text-white/40">
              Ask anything about your emails
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={newConversation}
              className="rounded-xl border border-white/10 px-3 py-2 text-xs font-medium text-white transition hover:bg-white/10"
            >
              + New Chat
            </button>

            <button
              type="button"
              onClick={() =>
                router.push("/inbox")
              }
              className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 text-white transition hover:bg-white/10"
              aria-label="Back to AI Inbox"
            >
              ×
            </button>
          </div>
        </header>

        {/* Error */}

        {error && (
          <div className="border-b border-red-400/20 bg-red-500/10 px-5 py-2.5 text-center text-xs text-red-300">
            {error}
          </div>
        )}

        {/* Chat */}

        <div className="min-h-0 flex-1">
          <ChatMessages
            messages={messages}
            isLoading={isLoading}
            onSuggestion={sendMessage}
            onOpenEmail={setSelectedEmail}
            onReplyEmail={handleReply}
            onRegenerate={regenerate}
          />
        </div>

        {/* Input */}

        <ChatInput
          onSend={sendMessage}
          disabled={isLoading}
        />
      </main>

      {/* =========================================================
          EMAIL DETAILS DRAWER
      ========================================================= */}

      <EmailDetailsDrawer
        email={selectedEmail}
        onClose={() =>
          setSelectedEmail(null)
        }
        onReply={handleReply}
      />
    </div>
  );
}