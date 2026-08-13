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
  createEmptyDraftState,
  applyDraftAction,
} from "../state/draftState";


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


/**
 * Extract the structured tool result.
 *
 * IMPORTANT:
 * Draft IDs and other structured action
 * information must come from tool_result.
 *
 * Never parse them from `answer`.
 */
function getToolResult(data) {
  return (
    data?.tool_result ??
    data?.toolResult ??
    null
  );
}


/**
 * Apply a backend tool response to DraftState.
 *
 * Only tool actions that actually return a
 * structured result are used here.
 */
function updateDraftFromResponse(
  currentDraft,
  data
) {
  const tool =
    data?.tool ??
    null;

  const toolResult =
    getToolResult(data);

  if (
    !tool ||
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


function normalizeAssistantMessage(
  data
) {
  return {
    id:
      crypto.randomUUID(),

    role: "assistant",

    content:
      getAssistantText(data),

    retrievedEmails:
      getRetrievedEmails(data)
        .map(normalizeEmail)
        .filter(
          (email) =>
            email?.id != null
        ),

    /**
     * Preserve structured tool information
     * on the message as well.
     *
     * This means ChatMessage can later inspect
     * the tool result without parsing answer.
     */
    tool:
      data?.tool ??
      null,

    toolResult:
      getToolResult(data),

    queryPlan:
      data?.query_plan ??
      data?.queryPlan ??
      null,

    timestamp:
      new Date().toISOString(),
  };
}


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

  /**
   * SINGLE SOURCE OF TRUTH FOR CURRENT DRAFT
   */
  const [
    draft,
    setDraft,
  ] = useState(
    createEmptyDraftState()
  );


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
            history.flatMap(
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

                return [
                  {
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

                    /**
                     * Preserve structured backend
                     * tool information when loading
                     * existing conversations.
                     */
                    tool:
                      message.tool ??
                      null,

                    toolResult:
                      message.tool_result ??
                      message.toolResult ??
                      null,

                    queryPlan:
                      message.query_plan ??
                      message.queryPlan ??
                      null,

                    timestamp:
                      message.created_at ??
                      message.createdAt ??
                      new Date().toISOString(),
                  },
                ];
              }
            );

          setMessages(normalized);

          /**
           * Recover the latest draft from
           * conversation history.
           *
           * We walk backwards so the most recent
           * tool result wins.
           */
          let recoveredDraft =
            createEmptyDraftState();

          for (
            let index =
              normalized.length - 1;
            index >= 0;
            index--
          ) {
            const message =
              normalized[index];

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

            recoveredDraft =
              applyDraftAction(
                recoveredDraft,
                message.tool,
                message.toolResult
              );

            /**
             * Once we find the latest draft
             * action, stop.
             */
            if (
              message.toolResult
                ?.draft_id != null
            ) {
              break;
            }
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

        const userMessage = {
          id:
            crypto.randomUUID(),

          role: "user",

          content: trimmed,

          retrievedEmails: [],

          tool: null,

          toolResult: null,

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

          const assistantMessage =
            normalizeAssistantMessage(
              data
            );

          setMessages(
            (previous) => [
              ...previous,
              assistantMessage,
            ]
          );

          /**
           * Update the SINGLE DraftState
           * from the structured tool response.
           */
          setDraft(
            (currentDraft) =>
              updateDraftFromResponse(
                currentDraft,
                data
              )
          );

          await loadConversations();
        } catch (err) {
          console.error(
            "Chat request failed:",
            err
          );

          setError(
            err?.response?.data
              ?.detail ??
              "Something went wrong while talking to your inbox."
          );
        } finally {
          setIsLoading(false);
        }
      },
      [
        activeConversationId,
        isLoading,
        loadConversations,
      ]
    );


  const newConversation =
    useCallback(() => {
      setActiveConversationId(
        null
      );

      setMessages([]);

      /**
       * New conversation means there is
       * no active draft.
       */
      setDraft(
        createEmptyDraftState()
      );

      setError(null);
    }, []);


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


  return {
    messages,
    conversations,

    activeConversationId,

    isLoading,
    isLoadingConversations,

    error,

    /**
     * Centralized DraftState.
     */
    draft,

    sendMessage,
    loadConversation,
    newConversation,
    regenerate,

    refreshConversations:
      loadConversations,
  };
}