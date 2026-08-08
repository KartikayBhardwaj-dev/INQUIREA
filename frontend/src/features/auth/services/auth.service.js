import api from "@/lib/axios";

export function loginWithGoogle() {
  window.location.href =
    `${process.env.NEXT_PUBLIC_API_URL}/auth/google/login`;
}

export async function getCurrentUser() {
  const response = await api.get("/auth/me");

  return response.data;
}

export async function logoutUser() {
  await api.post("/auth/logout");
}