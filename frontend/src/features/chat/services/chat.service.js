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


/* =========================================================
   GET COMPLETE GMAIL EMAIL
========================================================= */

export async function getEmailDetails(
  gmailMessageId
) {
  console.log(
    "📡 getEmailDetails SERVICE CALLED:",
    gmailMessageId
  );


  if (!gmailMessageId) {
    console.error(
      "🔴 getEmailDetails called WITHOUT Gmail message ID"
    );

    throw new Error(
      "Missing Gmail message ID"
    );
  }


  const url =
    `/gmail/email/${encodeURIComponent(
      gmailMessageId
    )}`;


  console.log(
    "📡 GETTING URL:",
    url
  );


  try {
    const response =
      await api.get(url);


    console.log(
      "✅ Gmail API response:",
      response.data
    );


    return response.data;

  } catch (error) {

    console.error(
      "❌ Gmail API request failed:",
      error
    );

    console.error(
      "❌ Gmail API request URL:",
      url
    );

    console.error(
      "❌ Gmail API status:",
      error?.response?.status
    );

    console.error(
      "❌ Gmail API response:",
      error?.response?.data
    );

    throw error;
  }
}