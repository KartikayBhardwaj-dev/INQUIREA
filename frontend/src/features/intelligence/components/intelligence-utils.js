export const CATEGORY_LABELS = {
  opportunity: "Opportunity",
  deadline: "Deadline",
  finance: "Finance",
  job: "Job",
  internship: "Internship",
  meeting: "Meeting",
  reply_required: "Reply Required",
  promotion: "Promotion",
  automated_notification: "Notification",
  personal: "Personal",
  other: "Other",
};

export const PRIORITY_LABELS = {
  urgent: "Urgent",
  high: "High",
  medium: "Medium",
  low: "Low",
};

export function getCategoryLabel(category) {
  return (
    CATEGORY_LABELS[category] ||
    "Other"
  );
}

export function getPriorityLabel(priority) {
  return (
    PRIORITY_LABELS[priority] ||
    "Unknown"
  );
}

export function requiresReply(item) {
  return Boolean(
    item?.extracted_data?.requires_reply
  );
}

export function getActionItems(item) {
  return (
    item?.extracted_data
      ?.extracted_entities
      ?.action_items || []
  );
}

export function getOrganizations(item) {
  return (
    item?.extracted_data
      ?.extracted_entities
      ?.organizations || []
  );
}

export function getPeople(item) {
  return (
    item?.extracted_data
      ?.extracted_entities
      ?.people || []
  );
}