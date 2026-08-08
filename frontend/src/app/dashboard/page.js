"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import LogoutButton from "@/features/auth/components/LogoutButton";
import useAuthStore from "@/stores/authStore";

export default function DashboardPage() {
  const router = useRouter();

  const user = useAuthStore(
    (state) => state.user
  );

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
      <main className="flex min-h-screen items-center justify-center">
        <p>Loading...</p>
      </main>
    );
  }

  if (!isLoggedIn) {
    return null;
  }

  return (
    <main className="min-h-screen p-8">
      <h1 className="text-3xl font-bold">
        Dashboard
      </h1>

      <p className="mt-2">
        Welcome to your AI workspace.
      </p>

      {user && (
        <div className="mt-6">
          <p>{user.email}</p>
        </div>
      )}
      <LogoutButton />
    </main>
  );
}