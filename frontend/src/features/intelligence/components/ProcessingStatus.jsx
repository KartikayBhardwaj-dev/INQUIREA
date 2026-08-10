"use client";

export default function ProcessingStatus({
  isSyncing,
  syncResult,
}) {
  if (!isSyncing && !syncResult) {
    return null;
  }

  if (isSyncing) {
    return (
      <div className="rounded-2xl border border-black/8 bg-white p-5">
        <div className="flex items-start gap-4">
          <div className="mt-1 h-2.5 w-2.5 animate-pulse rounded-full bg-black" />

          <div>
            <p className="text-sm font-medium">
              Syncing your inbox
            </p>

            <p className="mt-1 text-sm text-black/45">
              Fetching your recent emails and
              starting AI analysis.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-black/8 bg-white p-5">
      <p className="text-sm font-medium">
        AI analysis started
      </p>

      <p className="mt-1 text-sm text-black/45">
        {syncResult.emails_synced} new emails were
        found. INQUIREA is analyzing them in the
        background.
      </p>
    </div>
  );
}