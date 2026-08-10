"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import AppShell from "@/components/layout/AppShell";
import useAuthStore from "@/stores/authStore";


export default function AppLayout({ children }) {
  const router = useRouter();

  const isLoggedIn = useAuthStore(
    (state) => state.isLoggedIn
  );

  const isLoading = useAuthStore(
    (state) => state.isLoading
  );

  useEffect(() => {
    if (!isLoading && !isLoggedIn) {
      router.replace("/login");
    }
  }, [
    isLoading,
    isLoggedIn,
    router,
  ]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f7f7f5]">
        <div className="text-sm text-black/40">
          Loading workspace...
        </div>
      </div>
    );
  }

  if (!isLoggedIn) {
    return null;
  }

  return (
    <AppShell>
      {children}
    </AppShell>
  );
}