import api from "@/lib/axios";


// ============================================================
// Existing chat functions
// ============================================================

export async function createChat(
  message
) {
  const response =
    await api.post(
      "/chat",
      {
        message,
      }
    );

  return response.data;
}


export async function continueChat(
  conversationId,
  message
) {
  const response =
    await api.post(
      "/chat/continue",
      {
        conversation_id:
          conversationId,

        message,
      }
    );

  return response.data;
}


export async function getChatHistory(
  conversationId
) {
  const response =
    await api.get(
      `/chat/${conversationId}`
    );

  return response.data;
}


export async function getConversations() {
  const response =
    await api.get(
      "/chat/conversations"
    );

  return response.data;
}


// ============================================================
// TASK 31
// Draft editing through chat
// ============================================================

export async function editDraft(
  conversationId,
  draftId,
  content
) {
  const message =
    `Update draft ${draftId} with: ${content}`;

  return continueChat(
    conversationId,
    message
  );
}

// ============================================================
// TASK 34
// Save approved draft to Gmail
// ============================================================

export async function saveDraft(
  conversationId,
  draftId
) {
  const message =
    `Save draft ${draftId} to Gmail`;

  return continueChat(
    conversationId,
    message
  );
}