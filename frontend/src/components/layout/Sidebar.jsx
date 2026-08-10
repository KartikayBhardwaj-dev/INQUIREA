"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import UserProfile from "./UserProfile";

const navigation = [
  {
    name: "AI Inbox",
    href: "/inbox",
    icon: "✦",
  },
  {
    name: "Conversations",
    href: "/conversations",
    icon: "◉",
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-black/8 bg-white">
      {/* Logo */}
      <div className="px-7 pb-8 pt-7">
        <Link href="/dashboard" className="block">
          <div className="text-xl font-semibold tracking-tight">
            INQUIREA
          </div>

          <div className="mt-1 text-xs text-black/40">
            AI workspace
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4">
        <div className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-black/35">
          Workspace
        </div>

        <div className="space-y-1">
          {navigation.map((item) => {
            const active =
              pathname === item.href ||
              pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm transition ${
                  active
                    ? "bg-black text-white"
                    : "text-black/60 hover:bg-black/5 hover:text-black"
                }`}
              >
                <span className="text-base">
                  {item.icon}
                </span>

                <span>{item.name}</span>
              </Link>
            );
          })}
        </div>

        <div className="mb-3 mt-9 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-black/35">
          System
        </div>

        <Link
          href="/settings"
          className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm transition ${
            pathname.startsWith("/settings")
              ? "bg-black text-white"
              : "text-black/60 hover:bg-black/5 hover:text-black"
          }`}
        >
          <span>⚙</span>
          <span>Settings</span>
        </Link>
      </nav>

      <UserProfile />
    </aside>
  );
}