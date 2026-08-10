export function normalizeChatResponse(data) {
  if (!data) {
    return {
      conversationId: null,
      content: "",
      retrievedEmails: [],
    };
  }

  const conversationId =
    data.conversation_id ??
    data.conversationId ??
    data.conversation?.id ??
    null;

  const content =
    data.message ??
    data.response ??
    data.answer ??
    data.content ??
    data.output ??
    "";

  const retrievedEmails =
    data.retrieved_emails ??
    data.retrievedEmails ??
    data.emails ??
    [];

  return {
    conversationId,
    content:
      typeof content === "string"
        ? content
        : JSON.stringify(content),
    retrievedEmails: Array.isArray(
      retrievedEmails
    )
      ? retrievedEmails
      : [],
  };
}


export function normalizeHistory(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.messages)) {
    return data.messages;
  }

  if (Array.isArray(data?.history)) {
    return data.history;
  }

  if (Array.isArray(data?.conversation)) {
    return data.conversation;
  }

  return [];
}


export function normalizeMessage(message) {
  const role =
    message.role ??
    message.sender ??
    message.type ??
    "assistant";

  const content =
    message.content ??
    message.message ??
    message.text ??
    "";

  const retrievedEmails =
    message.retrieved_emails ??
    message.retrievedEmails ??
    message.emails ??
    [];

  return {
    id:
      message.id ??
      crypto.randomUUID(),

    role:
      role === "user"
        ? "user"
        : "assistant",

    content:
      typeof content === "string"
        ? content
        : JSON.stringify(content),

    retrievedEmails:
      Array.isArray(retrievedEmails)
        ? retrievedEmails
        : [],
  };
}


export function groupConversations(
  conversations
) {
  const now = new Date();

  const today = [];
  const yesterday = [];
  const lastWeek = [];
  const older = [];

  conversations.forEach((conversation) => {
    const date = new Date(
      conversation.updated_at ??
      conversation.updatedAt ??
      conversation.created_at ??
      conversation.createdAt ??
      now
    );

    const diff =
      now.getTime() - date.getTime();

    const days =
      diff / (1000 * 60 * 60 * 24);

    if (days < 1) {
      today.push(conversation);
    } else if (days < 2) {
      yesterday.push(conversation);
    } else if (days < 7) {
      lastWeek.push(conversation);
    } else {
      older.push(conversation);
    }
  });

  return {
    today,
    yesterday,
    lastWeek,
    older,
  };
}


export function getEmailId(email) {
  return (
    email.email_id ??
    email.emailId ??
    email.gmail_message_id ??
    email.gmailMessageId ??
    email.id ??
    null
  );
}


export function getEmailSubject(email) {
  return (
    email.subject ??
    email.title ??
    "No subject"
  );
}


export function getEmailSender(email) {
  return (
    email.sender ??
    email.from ??
    "Unknown sender"
  );
}


export function getEmailSummary(email) {
  return (
    email.summary ??
    email.snippet ??
    "No summary available."
  );
}


export function getEmailPriority(email) {
  return (
    email.priority ??
    "medium"
  );
}


export function getEmailCategory(email) {
  return (
    email.category ??
    "other"
  );
}