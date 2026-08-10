"use client";

import { useMemo } from "react";


function getDateGroup(dateValue) {
  if (!dateValue) {
    return "Older";
  }

  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return "Older";
  }

  const now = new Date();

  const today = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate()
  );

  const yesterday = new Date(today);

  yesterday.setDate(
    yesterday.getDate() - 1
  );

  const weekAgo = new Date(today);

  weekAgo.setDate(
    weekAgo.getDate() - 7
  );

  if (date >= today) {
    return "Today";
  }

  if (date >= yesterday) {
    return "Yesterday";
  }

  if (date >= weekAgo) {
    return "Last 7 days";
  }

  return "Older";
}


export default function ConversationSidebar({
  conversations = [],
  activeConversationId,
  onSelect,
  onNewConversation,
  isLoading,
}) {
  const grouped = useMemo(() => {
    const groups = {
      Today: [],
      Yesterday: [],
      "Last 7 days": [],
      Older: [],
    };

    conversations.forEach(
      (conversation) => {
        const group = getDateGroup(
          conversation.updated_at ??
            conversation.created_at
        );

        if (!groups[group]) {
          groups[group] = [];
        }

        groups[group].push(
          conversation
        );
      }
    );

    return groups;
  }, [conversations]);


  return (
    <aside className="flex h-full w-full shrink-0 flex-col border-r border-white/10 bg-black text-white">
      
      {/* ============================================================
          HEADER
      ============================================================ */}

      <div className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 px-4">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/40">
            INQUIREA
          </p>

          <p className="mt-1 text-sm font-semibold text-white">
            AI Inbox
          </p>
        </div>


        <button
          type="button"
          onClick={onNewConversation}
          className="rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-xs font-medium text-white transition hover:bg-white/10"
        >
          + New
        </button>
      </div>


      {/* ============================================================
          CONVERSATION LIST
      ============================================================ */}

      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        
        {/* Loading */}

        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4].map(
              (item) => (
                <div
                  key={`loading-${item}`}
                  className="h-11 animate-pulse rounded-xl bg-white/10"
                />
              )
            )}
          </div>
        ) : conversations.length === 0 ? (

          /* Empty */

          <div className="px-3 py-8 text-center">
            <div className="text-xl text-white">
              ✦
            </div>

            <p className="mt-2 text-xs text-white/40">
              No conversations yet.
            </p>

            <button
              type="button"
              onClick={onNewConversation}
              className="mt-4 rounded-xl border border-white/10 px-3 py-2 text-xs font-medium text-white/70 transition hover:bg-white/10 hover:text-white"
            >
              Start a conversation
            </button>
          </div>

        ) : (

          /* Conversation groups */

          Object.entries(grouped).map(
            ([group, items]) => {
              if (items.length === 0) {
                return null;
              }

              return (
                <div
                  key={`group-${group}`}
                  className="mb-5"
                >
                  {/* Group title */}

                  <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-white/30">
                    {group}
                  </p>


                  {/* Conversations */}

                  <div className="space-y-1">
                    {items.map(
                      (
                        conversation,
                        index
                      ) => {
                        const conversationId =
                          conversation.id ??
                          conversation.conversation_id ??
                          `conversation-${group}-${index}`;

                        const active =
                          String(
                            conversationId
                          ) ===
                          String(
                            activeConversationId
                          );


                        return (
                          <button
                            type="button"
                            key={
                              conversationId
                            }
                            onClick={() =>
                              onSelect?.(
                                conversationId
                              )
                            }
                            className={`w-full rounded-xl px-3 py-2.5 text-left transition ${
                              active
                                ? "bg-white text-black shadow-sm"
                                : "text-white/75 hover:bg-white/10 hover:text-white"
                            }`}
                          >
                            <div className="flex min-w-0 items-center gap-2">
                              
                              {/* AI icon */}

                              <span
                                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-[10px] font-semibold ${
                                  active
                                    ? "bg-black text-white"
                                    : "bg-white/10 text-white/60"
                                }`}
                              >
                                ✦
                              </span>


                              {/* Conversation title */}

                              <p
                                className={`min-w-0 truncate text-xs font-medium ${
                                  active
                                    ? "text-black"
                                    : "text-white/80"
                                }`}
                              >
                                {conversation.title ||
                                  "New conversation"}
                              </p>
                            </div>
                          </button>
                        );
                      }
                    )}
                  </div>
                </div>
              );
            }
          )
        )}
      </div>


      {/* ============================================================
          FOOTER
      ============================================================ */}

      <div className="shrink-0 border-t border-white/10 px-4 py-3">
        <p className="text-center text-[10px] text-white/25">
          Your AI email workspace
        </p>
      </div>
    </aside>
  );
}