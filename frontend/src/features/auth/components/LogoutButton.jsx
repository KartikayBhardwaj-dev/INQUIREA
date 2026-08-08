"use client";

import { useRouter } from "next/navigation";

import useAuthStore from "@/stores/authStore";
import { logoutUser } from "../services/auth.service";

export default function LogoutButton() {
  const router = useRouter();

  const clearUser = useAuthStore(
    (state) => state.clearUser
  );

  async function handleLogout() {
    try {
      await logoutUser();
    } finally {
      clearUser();
      router.replace("/login");
    }
  }

  return (
    <button
      onClick={handleLogout}
      className="rounded-lg border px-4 py-2"
    >
      Logout
    </button>
  );
}