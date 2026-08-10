import api from "@/lib/axios";


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
      `/chat/${conversationId}`,
      {
        message,
      }
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


export async function getChatHistory(
  conversationId
) {
  const response =
    await api.get(
      `/chat/history/${conversationId}`
    );

  return response.data;
}


export async function getEmailDetails(
  gmailMessageId
) {
  if (!gmailMessageId) {
    throw new Error(
      "Missing Gmail message ID"
    );
  }

  const response =
    await api.get(
      `/gmail/email/${encodeURIComponent(
        gmailMessageId
      )}`
    );

  return response.data;
}