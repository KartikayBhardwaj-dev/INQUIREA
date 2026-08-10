export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-black/35">
          System
        </p>

        <h1 className="mt-2 text-3xl font-semibold tracking-tight">
          Settings
        </h1>
      </div>

      <div className="rounded-2xl border border-black/8 bg-white p-6">
        <p className="font-medium">
          Workspace settings
        </p>

        <p className="mt-1 text-sm text-black/40">
          Settings will be added in a later phase.
        </p>
      </div>
    </div>
  );
}