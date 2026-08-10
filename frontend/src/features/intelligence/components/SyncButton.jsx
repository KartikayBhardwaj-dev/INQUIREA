"use client";

import { useSyncEmails } from "../hooks/useEmailIntelligence";


export default function SyncButton() {
  const syncMutation = useSyncEmails();

  const handleSync = () => {
    syncMutation.mutate();
  };

  return (
    <button
      onClick={handleSync}
      disabled={syncMutation.isPending}
      className="inline-flex items-center gap-2 rounded-xl bg-black px-4 py-2.5 text-sm font-medium text-white transition hover:bg-black/80 disabled:cursor-not-allowed disabled:opacity-50"
    >
      <span>
        {syncMutation.isPending ? "↻" : "↻"}
      </span>

      {syncMutation.isPending
        ? "Syncing..."
        : "Sync emails"}
    </button>
  );
}