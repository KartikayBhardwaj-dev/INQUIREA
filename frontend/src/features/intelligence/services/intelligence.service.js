import api from "@/lib/axios";

export async function getEmailIntelligence() {
  const response = await api.get("/email-intelligence/");

  return response.data;
}

export async function getEmailIntelligenceById(emailId) {
  const response = await api.get(
    `/email-intelligence/${emailId}`
  );

  return response.data;
}

export async function syncEmails(days = 7) {
  const response = await api.post(
    `/gmail/sync?days=${days}`
  );

  return response.data;
}