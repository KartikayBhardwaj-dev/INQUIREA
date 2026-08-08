"use client";

import { useEffect } from "react";

import useAuthStore from "@/stores/authStore";
import { getCurrentUser } from "../services/auth.service";

export default function AuthProvider({
  children,
}) {
  const setUser = useAuthStore(
    (state) => state.setUser
  );

  const clearUser = useAuthStore(
    (state) => state.clearUser
  );

  const setLoading = useAuthStore(
    (state) => state.setLoading
  );

  useEffect(() => {
    async function initializeAuth() {
      try {
        const user = await getCurrentUser();

        setUser(user);
      } catch {
        clearUser();
      } finally {
        setLoading(false);
      }
    }

    initializeAuth();
  }, [
    setUser,
    clearUser,
    setLoading,
  ]);

  return children;
}