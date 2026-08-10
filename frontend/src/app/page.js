"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import useAuthStore from "@/stores/authStore";


export default function Home() {
  const router = useRouter();

  const isLoggedIn = useAuthStore(
    (state) => state.isLoggedIn
  );

  const isLoading = useAuthStore(
    (state) => state.isLoading
  );

  useEffect(() => {
    if (isLoading) {
      return;
    }

    router.replace(
      isLoggedIn
        ? "/dashboard"
        : "/login"
    );
  }, [
    isLoading,
    isLoggedIn,
    router,
  ]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f7f7f5]">
      <p className="text-sm text-black/40">
        Loading INQUIREA...
      </p>
    </div>
  );
}