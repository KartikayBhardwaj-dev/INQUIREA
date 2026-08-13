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
// Backend response helpers
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
  return (
    data?.tool ??
    null
  );
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
// Draft action application
// ============================================================

/**
 * Apply one backend action to the centralized DraftState.
 *
 * IMPORTANT:
 *
 * Components must NOT interpret:
 *
 *   tool
 *   tool_result
 *
 * themselves.
 *
 * All action → DraftState conversion happens here.
 */
function updateDraftFromResponse(
  currentDraft,
  data
) {
  const tool = getTool(data);

  const toolResult = getToolResult(data);

  // No action.
  if (!tool) {
    return currentDraft;
  }

  // Tool failed.
  //
  // A failed tool must never modify the current
  // DraftState.
  if (
    data?.error ||
    data?.success === false
  ) {
    return currentDraft;
  }

  // No structured result.
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
  const tool = getTool(data);

  const toolResult =
    getToolResult(data);

  const action =
    normalizeToolAction(
      data,
      currentDraft
    );

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

    // --------------------------------------------------------
    // Structured action
    // --------------------------------------------------------

    action,

    tool,

    toolResult,

    // --------------------------------------------------------
    // Backend structured error
    // --------------------------------------------------------

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

  // ----------------------------------------------------------
  // Chat state
  // ----------------------------------------------------------

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


  // ----------------------------------------------------------
  // TASK 28
  //
  // Single source of truth for the active draft.
  // ----------------------------------------------------------

  const [
    draft,
    setDraft,
  ] = useState(
    createEmptyDraftState()
  );


  // ==========================================================
  // Load conversations
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
  // Load existing conversation
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


          // --------------------------------------------------
          // Normalize messages
          // --------------------------------------------------

          const normalized =
            history.map(
              (message) => {

                const role =
                  message.role ??
                  message.sender ??
                  "assistant";

                const content =
                  message.content ??
                  message.message ??
                  message.text ??
                  "";

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

                const error =
                  message.error ??
                  null;

                return {
                  id:
                    message.id ??
                    crypto.randomUUID(),

                  role:
                    role === "user"
                      ? "user"
                      : "assistant",

                  content,

                  retrievedEmails:
                    emails,

                  tool,

                  toolResult,

                  error,

                  queryPlan:
                    message.query_plan ??
                    message.queryPlan ??
                    null,

                  // Recreate renderer action
                  // from stored backend data.
                  action:
                    role === "assistant"
                      ? normalizeToolAction(
                          message,
                          null
                        )
                      : null,

                  timestamp:
                    message.created_at ??
                    message.createdAt ??
                    new Date().toISOString(),
                };
              }
            );


          setMessages(normalized);


          // --------------------------------------------------
          // TASK 28
          //
          // Reconstruct DraftState from the conversation.
          //
          // We replay successful draft actions in chronological
          // order so the final state represents the current
          // draft.
          // --------------------------------------------------

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

            if (!message.tool) {
              continue;
            }

            if (
              !message.toolResult ||
              typeof message.toolResult !==
                "object"
            ) {
              continue;
            }

            // Failed actions must not mutate state.
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
  // Send message
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
          return;
        }

        setError(null);


        // ----------------------------------------------------
        // Add user message immediately
        // ----------------------------------------------------

        const userMessage = {
          id:
            crypto.randomUUID(),

          role: "user",

          content:
            trimmed,

          retrievedEmails: [],

          tool: null,

          toolResult: null,

          error: null,

          action: null,

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


          // --------------------------------------------------
          // Backend request
          // --------------------------------------------------

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


          // --------------------------------------------------
          // Conversation ID
          // --------------------------------------------------

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


          // --------------------------------------------------
          // TASK 29
          //
          // Normalize backend action in ONE place.
          // --------------------------------------------------

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


          // --------------------------------------------------
          // TASK 28
          //
          // Update the single DraftState.
          //
          // This is the ONLY place where the active draft
          // changes because of a chat action.
          // --------------------------------------------------

          setDraft(
            (currentDraft) =>
              updateDraftFromResponse(
                currentDraft,
                data
              )
          );


          // --------------------------------------------------
          // Backend structured error
          // --------------------------------------------------

          if (data?.error) {

            setError(
              data.error.message ??
              data.error.code ??
              "The requested action could not be completed."
            );
          }


          await loadConversations();

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
  // New conversation
  // ==========================================================

  const newConversation =
    useCallback(() => {

      setActiveConversationId(
        null
      );

      setMessages([]);

      // New conversation = no active draft.
      setDraft(
        createEmptyDraftState()
      );

      setError(null);

    }, []);


  // ==========================================================
  // Regenerate
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

    // Chat
    messages,
    conversations,

    activeConversationId,

    isLoading,
    isLoadingConversations,

    error,


    // --------------------------------------------------------
    // TASK 28
    // --------------------------------------------------------

    /**
     * Current centralized DraftState.
     *
     * Components should consume this instead of
     * interpreting tool responses themselves.
     */
    draft,


    // --------------------------------------------------------
    // Actions
    // --------------------------------------------------------

    sendMessage,

    loadConversation,

    newConversation,

    regenerate,

    refreshConversations:
      loadConversations,
  };
}