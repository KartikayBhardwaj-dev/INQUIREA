// ============================================================
// Chat Error Mapper
// ============================================================
//
// Converts backend error codes into user-friendly messages.
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


  // Example:
  // "APPROVAL_REQUIRED"

  if (typeof error === "string") {
    return error;
  }


  // Possible backend formats:
  //
  // { code: "APPROVAL_REQUIRED" }
  //
  // { error: { code: "APPROVAL_REQUIRED" } }
  //
  // { detail: { code: "APPROVAL_REQUIRED" } }

  return (
    error?.code ??
    error?.error?.code ??
    error?.detail?.code ??
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


  // Known backend error
  if (
    code &&
    CHAT_ERROR_MESSAGES[code]
  ) {
    return CHAT_ERROR_MESSAGES[code];
  }


  // Unknown backend error with a message
  const message =
    getErrorMessage(error);


  if (message) {
    return message;
  }


  return DEFAULT_ERROR_MESSAGE;
}


export default getFriendlyChatError;