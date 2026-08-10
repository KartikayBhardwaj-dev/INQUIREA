"use client";

import { useState } from "react";

import SyncButton from "@/features/intelligence/components/SyncButton";
import ProcessingStatus from "@/features/intelligence/components/ProcessingStatus";
import IntelligenceStats from "@/features/intelligence/components/IntelligenceStats";
import AttentionNeeded from "@/features/intelligence/components/AttentionNeeded";

import {
  useEmailIntelligence,
  useSyncEmails,
} from "@/features/intelligence/hooks/useEmailIntelligence";

import useAuthStore from "@/stores/authStore";


export default function DashboardPage() {
  const user = useAuthStore(
    (state) => state.user
  );

  const {
    data = [],
    isLoading,
    isError,
  } = useEmailIntelligence();

  const syncMutation = useSyncEmails();

  const firstName =
    user?.name?.split(" ")[0] ||
    user?.email?.split("@")[0] ||
    "there";

  return (
    <div className="space-y-10">
      {/* Header */}
      <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-black/35">
            AI Workspace
          </p>

          <h1 className="mt-2 text-4xl font-semibold tracking-tight">
            Welcome back, {firstName}.
          </h1>

          <p className="mt-2 max-w-xl text-sm leading-6 text-black/45">
            INQUIREA turns your inbox into decisions,
            priorities and actions.
          </p>
        </div>

        <SyncButton />
      </section>

      {/* Processing */}
      <ProcessingStatus
        isSyncing={syncMutation.isPending}
        syncResult={syncMutation.data}
      />

      {/* Loading */}
      {isLoading && (
        <div className="rounded-2xl border border-black/8 bg-white p-8">
          <div className="animate-pulse text-sm text-black/40">
            Understanding your inbox...
          </div>
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="rounded-2xl border border-black/10 bg-white p-6">
          <p className="font-medium">
            We couldn't load your intelligence.
          </p>

          <p className="mt-1 text-sm text-black/40">
            Please try refreshing the page.
          </p>
        </div>
      )}

      {!isLoading && !isError && (
        <>
          {/* Empty state */}
          {data.length === 0 ? (
            <EmptyDashboard />
          ) : (
            <>
              {/* Stats */}
              <section>
                <div className="mb-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-black/35">
                    Intelligence
                  </p>

                  <h2 className="mt-1 text-xl font-semibold tracking-tight">
                    Your inbox at a glance
                  </h2>
                </div>

                <IntelligenceStats data={data} />
              </section>

              {/* Attention */}
              <AttentionNeeded data={data} />

              {/* AI activity */}
              <AIActivity data={data} />
            </>
          )}
        </>
      )}
    </div>
  );
}


function EmptyDashboard() {
  return (
    <div className="rounded-3xl border border-dashed border-black/10 bg-white px-8 py-20 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-black text-xl text-white">
        ✦
      </div>

      <h2 className="mt-6 text-2xl font-semibold tracking-tight">
        Let's understand your inbox.
      </h2>

      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-black/45">
        Sync your recent emails and INQUIREA will
        analyze priorities, deadlines, meetings,
        opportunities and actions for you.
      </p>

      <div className="mt-6">
        <span className="text-sm font-medium text-black/60">
          Use "Sync emails" above to begin.
        </span>
      </div>
    </div>
  );
}


function AIActivity({ data }) {
  const replyCount = data.filter(
    (item) =>
      item.extracted_data?.requires_reply === true
  ).length;

  const meetingCount = data.filter(
    (item) => item.category === "meeting"
  ).length;

  const deadlineCount = data.filter(
    (item) => item.category === "deadline"
  ).length;

  return (
    <section>
      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-black/35">
          AI Activity
        </p>

        <h2 className="mt-1 text-xl font-semibold tracking-tight">
          What INQUIREA discovered
        </h2>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <ActivityItem
          value={data.length}
          label="emails understood"
        />

        <ActivityItem
          value={replyCount}
          label="replies detected"
        />

        <ActivityItem
          value={meetingCount + deadlineCount}
          label="events and deadlines"
        />
      </div>
    </section>
  );
}


function ActivityItem({
  value,
  label,
}) {
  return (
    <div className="rounded-2xl border border-black/8 bg-white p-5">
      <div className="text-2xl font-semibold">
        {value}
      </div>

      <div className="mt-1 text-sm text-black/40">
        {label}
      </div>
    </div>
  );
}