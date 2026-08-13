"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  createChat,
  continueChat,
  getChatHistory,
  getConversations,
} from "../services/chat.service";

import {
  normalizeToolAction,
} from "../utils/actionRenderer";

import {
  createEmptyDraftState,
  applyDraftAction,
} from "../state/draftState";


// ============================================================
// Backend helpers
// ============================================================

function getConversationId(data) {
  return (
    data?.conversation_id ??
    data?.conversationId ??
    data?.conversation?.id ??
    null
  );
}


function getAssistantText(data) {
  return (
    data?.response ??
    data?.answer ??
    data?.message ??
    data?.content ??
    data?.assistant_message ??
    ""
  );
}


function getRetrievedEmails(data) {
  return (
    data?.retrieved_emails ??
    data?.retrievedEmails ??
    data?.emails ??
    []
  );
}


function getTool(data) {
  return data?.tool ?? null;
}


function getToolResult(data) {
  return (
    data?.tool_result ??
    data?.toolResult ??
    null
  );
}


// ============================================================
// Email normalization
// ============================================================

function normalizeEmail(email) {
  if (!email) {
    return null;
  }

  return {
    id:
      email.id ??
      email.email_id ??
      email.emailId,

    email_id:
      email.email_id ??
      email.id ??
      email.emailId,

    gmail_message_id:
      email.gmail_message_id ??
      email.gmailMessageId ??
      email.message_id ??
      email.messageId ??
      null,

    subject:
      email.subject ??
      "Untitled email",

    sender:
      email.sender ??
      email.from ??
      email.sender_email ??
      "Unknown sender",

    recipient:
      email.recipient ??
      email.to ??
      null,

    received_at:
      email.received_at ??
      email.receivedAt ??
      email.date ??
      null,

    summary:
      email.summary ??
      email.ai_summary ??
      email.snippet ??
      "",

    priority:
      email.priority ??
      "normal",

    category:
      email.category ??
      "other",

    requires_reply:
      email.requires_reply ??
      email.requiresReply ??
      email.reply_required ??
      false,

    snippet:
      email.snippet ??
      "",

    body:
      email.body ??
      email.content ??
      null,

    tags:
      email.tags ??
      email.labels ??
      [],
  };
}


// ============================================================
// Draft response application
// ============================================================

function updateDraftFromResponse(
  currentDraft,
  data
) {
  const tool = getTool(data);

  const toolResult =
    getToolResult(data);

  if (!tool) {
    return currentDraft;
  }

  if (
    data?.success === false ||
    data?.error
  ) {
    return currentDraft;
  }

  if (
    !toolResult ||
    typeof toolResult !== "object"
  ) {
    return currentDraft;
  }

  return applyDraftAction(
    currentDraft,
    tool,
    toolResult
  );
}


// ============================================================
// Assistant message normalization
// ============================================================

function normalizeAssistantMessage(
  data,
  currentDraft
) {
  const retrievedEmails =
    getRetrievedEmails(data)
      .map(normalizeEmail)
      .filter(
        (email) =>
          email?.id != null
      );

  return {
    id:
      crypto.randomUUID(),

    role: "assistant",

    content:
      getAssistantText(data),

    retrievedEmails,

    tool:
      getTool(data),

    toolResult:
      getToolResult(data),

    action:
      normalizeToolAction(
        data,
        currentDraft
      ),

    error:
      data?.error ??
      null,

    queryPlan:
      data?.query_plan ??
      data?.queryPlan ??
      null,

    timestamp:
      new Date().toISOString(),
  };
}


// ============================================================
// Conversation normalization
// ============================================================

function normalizeConversation(
  conversation
) {
  return {
    id:
      conversation.id ??
      conversation.conversation_id ??
      conversation.conversationId,

    title:
      conversation.title ??
      conversation.name ??
      conversation.subject ??
      "New conversation",

    created_at:
      conversation.created_at ??
      conversation.createdAt ??
      null,

    updated_at:
      conversation.updated_at ??
      conversation.updatedAt ??
      null,
  };
}


// ============================================================
// Hook
// ============================================================

export default function useChat() {

  const [
    messages,
    setMessages,
  ] = useState([]);

  const [
    conversations,
    setConversations,
  ] = useState([]);

  const [
    activeConversationId,
    setActiveConversationId,
  ] = useState(null);

  const [
    isLoading,
    setIsLoading,
  ] = useState(false);

  const [
    isLoadingConversations,
    setIsLoadingConversations,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState(null);


  // ==========================================================
  // SINGLE DRAFT STATE
  // ==========================================================

  const [
    draft,
    setDraft,
  ] = useState(
    createEmptyDraftState()
  );


  // ==========================================================
  // Conversations
  // ==========================================================

  const loadConversations =
    useCallback(async () => {

      try {

        setIsLoadingConversations(
          true
        );

        const data =
          await getConversations();

        const list =
          Array.isArray(data)
            ? data
            : data?.conversations ??
              [];

        setConversations(
          list.map(
            normalizeConversation
          )
        );

      } catch (err) {

        console.error(
          "Failed to load conversations:",
          err
        );

      } finally {

        setIsLoadingConversations(
          false
        );
      }

    }, []);


  useEffect(() => {
    loadConversations();
  }, [loadConversations]);


  // ==========================================================
  // Load conversation
  // ==========================================================

  const loadConversation =
    useCallback(
      async (conversationId) => {

        if (!conversationId) {
          return;
        }

        try {

          setError(null);
          setIsLoading(true);

          const data =
            await getChatHistory(
              conversationId
            );

          const history =
            Array.isArray(data)
              ? data
              : data?.messages ??
                data?.history ??
                [];


          const normalized =
            history.map(
              (message) => {

                const role =
                  message.role ??
                  message.sender ??
                  "assistant";

                const emails =
                  (
                    message.retrieved_emails ??
                    message.retrievedEmails ??
                    message.emails ??
                    []
                  )
                    .map(normalizeEmail)
                    .filter(
                      (email) =>
                        email?.id != null
                    );

                const tool =
                  message.tool ??
                  null;

                const toolResult =
                  message.tool_result ??
                  message.toolResult ??
                  null;

                return {
                  id:
                    message.id ??
                    crypto.randomUUID(),

                  role:
                    role === "user"
                      ? "user"
                      : "assistant",

                  content:
                    message.content ??
                    message.message ??
                    message.text ??
                    "",

                  retrievedEmails:
                    emails,

                  tool,

                  toolResult,

                  action:
                    role === "assistant"
                      ? normalizeToolAction(
                          message,
                          null
                        )
                      : null,

                  error:
                    message.error ??
                    null,

                  queryPlan:
                    message.query_plan ??
                    message.queryPlan ??
                    null,

                  timestamp:
                    message.created_at ??
                    message.createdAt ??
                    new Date().toISOString(),
                };
              }
            );


          setMessages(
            normalized
          );


          // ----------------------------------------------------
          // Replay tool actions
          // ----------------------------------------------------

          let recoveredDraft =
            createEmptyDraftState();

          for (
            const message of normalized
          ) {

            if (
              message.role !==
              "assistant"
            ) {
              continue;
            }

            if (
              !message.tool ||
              !message.toolResult
            ) {
              continue;
            }

            if (message.error) {
              continue;
            }

            recoveredDraft =
              applyDraftAction(
                recoveredDraft,
                message.tool,
                message.toolResult
              );
          }

          setDraft(
            recoveredDraft
          );

          setActiveConversationId(
            conversationId
          );

        } catch (err) {

          console.error(
            "Failed to load chat:",
            err
          );

          setError(
            "Unable to load this conversation."
          );

        } finally {

          setIsLoading(false);
        }

      },
      []
    );


  // ==========================================================
  // Generic chat request
  // ==========================================================

  const sendMessage =
    useCallback(
      async (text) => {

        const trimmed =
          text?.trim();

        if (
          !trimmed ||
          isLoading
        ) {
          return null;
        }

        setError(null);

        const userMessage = {
          id:
            crypto.randomUUID(),

          role: "user",

          content:
            trimmed,

          retrievedEmails: [],

          tool: null,

          toolResult: null,

          action: null,

          error: null,

          queryPlan: null,

          timestamp:
            new Date().toISOString(),
        };

        setMessages(
          (previous) => [
            ...previous,
            userMessage,
          ]
        );

        setIsLoading(true);

        try {

          let data;

          if (
            activeConversationId
          ) {

            data =
              await continueChat(
                activeConversationId,
                trimmed
              );

          } else {

            data =
              await createChat(
                trimmed
              );
          }


          const conversationId =
            getConversationId(data);

          if (
            conversationId &&
            !activeConversationId
          ) {
            setActiveConversationId(
              conversationId
            );
          }


          // Use current draft snapshot for
          // action rendering.
          const assistantMessage =
            normalizeAssistantMessage(
              data,
              draft
            );

          setMessages(
            (previous) => [
              ...previous,
              assistantMessage,
            ]
          );


          setDraft(
            (currentDraft) =>
              updateDraftFromResponse(
                currentDraft,
                data
              )
          );


          if (data?.error) {

            setError(
              data.error.message ??
              data.error.code ??
              "The requested action could not be completed."
            );
          }


          await loadConversations();

          return data;

        } catch (err) {

          console.error(
            "Chat request failed:",
            err
          );

          setError(
            err?.response?.data
              ?.detail ??
            err?.response?.data
              ?.error?.message ??
            "Something went wrong while talking to your inbox."
          );

          return null;

        } finally {

          setIsLoading(false);
        }

      },
      [
        activeConversationId,
        isLoading,
        draft,
        loadConversations,
      ]
    );


  // ==========================================================
  // TASK 31 — Edit draft
  // ==========================================================

  const editDraft =
    useCallback(
      async (content) => {

        if (!draft?.draft_id) {
          setError(
            "No active draft is available."
          );
          return;
        }

        const message =
          `Update draft ${draft.draft_id} with: ${content}`;

        await sendMessage(message);
      },
      [
        draft?.draft_id,
        sendMessage,
      ]
    );


  // ==========================================================
  // Regenerate draft
  // ==========================================================

  const regenerateDraft =
    useCallback(
      async () => {

        if (!draft?.draft_id) {
          setError(
            "No active draft is available."
          );
          return;
        }

        await sendMessage(
          `Regenerate draft ${draft.draft_id}`
        );
      },
      [
        draft?.draft_id,
        sendMessage,
      ]
    );


  // ==========================================================
  // Approve draft
  // ==========================================================

  const approveDraft =
    useCallback(
      async () => {

        if (!draft?.draft_id) {
          setError(
            "No active draft is available."
          );
          return;
        }

        await sendMessage(
          `Approve draft ${draft.draft_id}`
        );
      },
      [
        draft?.draft_id,
        sendMessage,
      ]
    );


  // ==========================================================
  // Reject draft
  // ==========================================================

  const rejectDraft =
    useCallback(
      async () => {

        if (!draft?.draft_id) {
          setError(
            "No active draft is available."
          );
          return;
        }

        await sendMessage(
          `Reject draft ${draft.draft_id}`
        );
      },
      [
        draft?.draft_id,
        sendMessage,
      ]
    );


  // ==========================================================
  // Send draft
  // ==========================================================

  const sendDraft =
    useCallback(
      async () => {

        if (!draft?.draft_id) {
          setError(
            "No active draft is available."
          );
          return;
        }

        await sendMessage(
          `Send draft ${draft.draft_id}`
        );
      },
      [
        draft?.draft_id,
        sendMessage,
      ]
    );


  // ==========================================================
  // New conversation
  // ==========================================================

  const newConversation =
    useCallback(() => {

      setActiveConversationId(
        null
      );

      setMessages([]);

      setDraft(
        createEmptyDraftState()
      );

      setError(null);

    }, []);


  // ==========================================================
  // Regenerate AI message
  // ==========================================================

  const regenerate =
    useCallback(
      async (messageIndex) => {

        if (
          isLoading ||
          messageIndex < 1
        ) {
          return;
        }

        const previousUserMessage =
          [...messages]
            .slice(
              0,
              messageIndex
            )
            .reverse()
            .find(
              (message) =>
                message.role ===
                "user"
            );

        if (
          !previousUserMessage
        ) {
          return;
        }

        setMessages(
          (previous) =>
            previous.slice(
              0,
              messageIndex
            )
        );

        await sendMessage(
          previousUserMessage.content
        );

      },
      [
        messages,
        isLoading,
        sendMessage,
      ]
    );


  // ==========================================================
  // Public API
  // ==========================================================

  return {

    messages,
    conversations,

    activeConversationId,

    isLoading,
    isLoadingConversations,

    error,

    // Centralized draft
    draft,

    // Chat
    sendMessage,

    // Draft actions
    editDraft,
    regenerateDraft,
    approveDraft,
    rejectDraft,
    sendDraft,

    // Conversation
    loadConversation,
    newConversation,

    regenerate,

    refreshConversations:
      loadConversations,
  };
}