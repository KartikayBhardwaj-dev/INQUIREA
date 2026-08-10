"use client";

import Sidebar from "./Sidebar.jsx";

export default function AppShell({ children }) {
  return (
    <div className="min-h-screen bg-[#f7f7f5] text-[#171717]">
      <Sidebar />

      <main className="min-h-screen pl-64">
        <div className="mx-auto max-w-[1600px] px-8 py-7">
          {children}
        </div>
      </main>
    </div>
  );
}