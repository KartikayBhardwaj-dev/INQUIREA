// ============================================================
// Chat Error Mapper
// ============================================================

const CHAT_ERROR_MESSAGES = {
  APPROVAL_REQUIRED:
    "Please approve the draft before sending.",

  DRAFT_NOT_FOUND:
    "This draft no longer exists.",

  GMAIL_AUTH_ERROR:
    "Your Gmail connection needs to be refreshed.",

  GMAIL_API_ERROR:
    "Gmail could not complete this action. Please try again.",

  GMAIL_DRAFT_NOT_FOUND:
    "The Gmail draft no longer exists. Please save the draft again.",

  SEND_FAILED:
    "The email could not be sent. Please try again.",
};


const DEFAULT_ERROR_MESSAGE =
  "Something went wrong while talking to your inbox.";


// ============================================================
// Extract error code
// ============================================================

function getErrorCode(error) {

  if (!error) {
    return null;
  }


  if (typeof error === "string") {
    return error;
  }


  return (
    error?.code ??
    error?.error_code ??
    error?.errorCode ??
    error?.error?.code ??
    error?.error?.error_code ??
    error?.detail?.code ??
    error?.detail?.error_code ??
    error?.detail?.errorCode ??
    null
  );
}


// ============================================================
// Extract backend message
// ============================================================

function getErrorMessage(error) {

  if (!error) {
    return null;
  }


  if (typeof error === "string") {
    return error;
  }


  return (
    error?.message ??
    error?.error?.message ??
    error?.detail?.message ??
    (
      typeof error?.detail === "string"
        ? error.detail
        : null
    ) ??
    null
  );
}


// ============================================================
// Public mapper
// ============================================================

export function getFriendlyChatError(error) {

  if (!error) {
    return DEFAULT_ERROR_MESSAGE;
  }


  const code =
    getErrorCode(error);


  if (
    code &&
    CHAT_ERROR_MESSAGES[code]
  ) {
    return CHAT_ERROR_MESSAGES[code];
  }


  const message =
    getErrorMessage(error);


  if (message) {
    return message;
  }


  return DEFAULT_ERROR_MESSAGE;
}


export default getFriendlyChatError;