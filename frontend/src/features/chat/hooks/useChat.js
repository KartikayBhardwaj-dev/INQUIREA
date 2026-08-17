"use client";

import {
  useCallback,
  useEffect,
  useRef,
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
  getFriendlyChatError,
} from "../utils/errorMapper";

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
  const tool =
    getTool(data);

  const toolResult =
    getToolResult(data);

  if (!tool) {
    return currentDraft;
  }

  // Do not modify the existing draft when
  // backend reports an error.
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

    role:
      "assistant",

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
// TASK 37 — Loading labels
// ============================================================

const LOADING_LABELS = {
  sendMessage: "Sending...",
  editDraft: "Saving...",
  regenerateDraft: "Generating...",
  approveDraft: "Approving...",
  rejectDraft: "Rejecting...",
  saveDraftToGmail: "Saving...",
  sendDraft: "Sending...",
  regenerate: "Generating...",
  loadConversation: "Loading...",
};


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


  // ==========================================================
  // Legacy/general loading state
  // ==========================================================

  const [
    isLoading,
    setIsLoading,
  ] = useState(false);


  // ==========================================================
  // TASK 37 — Action-specific loading
  // ==========================================================

  const [
    loadingAction,
    setLoadingAction,
  ] = useState(null);


  /*
   * IMPORTANT:
   *
   * A ref is used as the actual synchronous lock.
   *
   * React state updates are asynchronous. Therefore:
   *
   *   click -> click
   *
   * could otherwise happen before `loadingAction` visually
   * updates.
   *
   * This ref prevents duplicate backend operations immediately.
   */
  const actionLockRef =
    useRef(false);


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
  // TASK 37 — Start action
  // ==========================================================

  const startAction =
    useCallback(
      (actionName) => {

        /*
         * Hard synchronous lock.
         *
         * This is what protects Send and other backend
         * operations against duplicate clicks.
         */
        if (actionLockRef.current) {
          return false;
        }


        actionLockRef.current = true;


        setLoadingAction(
          actionName
        );


        setIsLoading(true);


        return true;

      },
      []
    );


  // ==========================================================
  // TASK 37 — Finish action
  // ==========================================================

  const finishAction =
    useCallback(() => {

      actionLockRef.current =
        false;


      setLoadingAction(null);


      setIsLoading(false);

    }, []);


  // ==========================================================
  // TASK 37 — Loading helpers
  // ==========================================================

  const isActionLoading =
    useCallback(
      (actionName) =>
        loadingAction === actionName,
      [loadingAction]
    );


  const getLoadingLabel =
    useCallback(
      (actionName = loadingAction) =>
        LOADING_LABELS[actionName] ??
        "Loading...",
      [loadingAction]
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


        /*
         * Do not allow a conversation switch while another
         * backend action is running.
         */
        if (actionLockRef.current) {
          return;
        }


        if (
          !startAction(
            "loadConversation"
          )
        ) {
          return;
        }


        try {

          setError(null);


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
            getFriendlyChatError(
              err?.response?.data ??
              err
            )
          );

        } finally {

          finishAction();

        }

      },
      [
        startAction,
        finishAction,
      ]
    );


  // ==========================================================
  // Generic chat request
  // ==========================================================

  const sendMessage =
    useCallback(
      async (
        text,
        actionName = "sendMessage"
      ) => {

        const trimmed =
          text?.trim();


        if (!trimmed) {
          return null;
        }


        /*
         * TASK 37:
         *
         * This is the central duplicate-operation protection.
         *
         * Every action which ultimately calls sendMessage()
         * passes through this lock.
         */
        if (
          !startAction(
            actionName
          )
        ) {
          return null;
        }


        setError(null);


        const userMessage = {
          id:
            crypto.randomUUID(),

          role:
            "user",

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


          // ==================================================
          // TASK 36 — Backend error handling
          // ==================================================

          if (
            data?.success === false ||
            data?.error
          ) {

            setError(
              getFriendlyChatError(
                data?.error ??
                data
              )
            );

          }


          // ==================================================
          // Draft processing
          // ==================================================

          const nextDraft =
            updateDraftFromResponse(
              draft,
              data
            );


          const assistantMessage =
            normalizeAssistantMessage(
              data,
              nextDraft
            );


          setMessages(
            (previous) => [
              ...previous,
              assistantMessage,
            ]
          );


          setDraft(
            nextDraft
          );


          await loadConversations();


          return data;

        } catch (err) {

          console.error(
            "Chat request failed:",
            err
          );


          setError(
            getFriendlyChatError(
              err?.response?.data ??
              err
            )
          );


          return null;

        } finally {

          finishAction();

        }

      },
      [
        activeConversationId,
        draft,
        loadConversations,
        startAction,
        finishAction,
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

          return null;
        }


        return sendMessage(
          `Update draft ${draft.draft_id} with: ${content}`,
          "editDraft"
        );

      },
      [
        draft?.draft_id,
        sendMessage,
      ]
    );


  // ==========================================================
  // TASK 32 — Regenerate draft
  // ==========================================================

  const regenerateDraft =
    useCallback(
      async () => {

        if (!draft?.draft_id) {

          setError(
            "No active draft is available."
          );

          return null;
        }


        const draftId =
          draft.draft_id;


        return sendMessage(
          `Regenerate draft ${draftId}`,
          "regenerateDraft"
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

          return null;
        }


        return sendMessage(
          `Approve draft ${draft.draft_id}`,
          "approveDraft"
        );

      },
      [
        draft?.draft_id,
        sendMessage,
      ]
    );


  // ==========================================================
  // TASK 34 — Save draft to Gmail
  // ==========================================================

  const saveDraftToGmail =
    useCallback(
      async () => {

        if (!draft?.draft_id) {

          setError(
            "No active draft is available."
          );

          return null;
        }


        if (
          draft.approval_status !==
          "APPROVED"
        ) {

          setError(
            "Draft must be approved before saving to Gmail."
          );

          return null;
        }


        if (draft.gmail_draft_id) {
          return null;
        }


        return sendMessage(
          `Save draft ${draft.draft_id} to Gmail`,
          "saveDraftToGmail"
        );

      },
      [
        draft?.draft_id,
        draft?.approval_status,
        draft?.gmail_draft_id,
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

          return null;
        }


        return sendMessage(
          `Reject draft ${draft.draft_id}`,
          "rejectDraft"
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

          return null;
        }


        return sendMessage(
          `Send draft ${draft.draft_id}`,
          "sendDraft"
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

      /*
       * Prevent changing conversation while a backend
       * operation is running.
       */
      if (actionLockRef.current) {
        return;
      }


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
          messageIndex < 1
        ) {
          return null;
        }


        /*
         * The actual synchronous duplicate protection happens
         * inside sendMessage().
         */
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
          return null;
        }


        /*
         * Don't remove the message until the action has actually
         * acquired the lock.
         */
        if (
          actionLockRef.current
        ) {
          return null;
        }


        setMessages(
          (previous) =>
            previous.slice(
              0,
              messageIndex
            )
        );


        return sendMessage(
          previousUserMessage.content,
          "regenerate"
        );

      },
      [
        messages,
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

    // General loading
    isLoading,

    isLoadingConversations,

    // TASK 37
    loadingAction,

    isActionLoading,

    getLoadingLabel,

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
    saveDraftToGmail,
    sendDraft,

    // Conversation
    loadConversation,
    newConversation,

    regenerate,

    refreshConversations:
      loadConversations,
  };
}