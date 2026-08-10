"use client";

import LogoutButton from "@/features/auth/components/LogoutButton";
import useAuthStore from "@/stores/authStore";

export default function UserProfile() {
  const user = useAuthStore(
    (state) => state.user
  );

  return (
    <div className="border-t border-black/8 p-4">
      <div className="flex items-center gap-3 rounded-xl p-2">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-black text-sm font-medium text-white">
          {user?.email?.charAt(0)?.toUpperCase() || "U"}
        </div>

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">
            {user?.name || "User"}
          </p>

          <p className="truncate text-xs text-black/40">
            {user?.email || ""}
          </p>
        </div>
      </div>

      <div className="mt-2 px-2">
        <LogoutButton />
      </div>
    </div>
  );
}