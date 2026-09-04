"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { API_URL } from "@/lib/auth";
import type { CurrentUser } from "@/lib/auth";

type AppHeaderProps = {
  user?: CurrentUser | null;
};

export function AppHeader({ user }: AppHeaderProps) {
  async function handleLogout() {
    await fetch(`${API_URL}/auth/logout`, {
      method: "POST",
      credentials: "include",
    }).catch(() => {});
    window.location.href = "/";
  }

  return (
    <header className="border-b border-white/10 bg-[#071827] px-6 py-4">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
        <div className="flex items-center gap-6">
          <Link href="/dashboard">
            <img
              alt="Clavis"
              className="h-auto w-32"
              height="105"
              src="/clavis-logo.svg"
              width="301"
            />
          </Link>
          <nav className="hidden items-center gap-1 sm:flex">
            <NavLink href="/dashboard">Projetos</NavLink>
            <NavLink href="/dashboard/api-keys">API Keys</NavLink>
            {user?.role === "admin" && (
              <NavLink href="/dashboard/admin">Admin</NavLink>
            )}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          {user ? (
            <span className="hidden text-xs text-slate-500 md:block">
              {user.full_name ?? user.email}
            </span>
          ) : null}
          <button
            className="h-10 border border-white/15 px-4 text-sm font-medium text-slate-200 transition hover:border-cyan-300 hover:text-cyan-200"
            onClick={handleLogout}
            type="button"
          >
            Sair
          </button>
        </div>
      </div>
    </header>
  );
}

function NavLink({ href, children }: { href: string; children: ReactNode }) {
  const pathname = usePathname();
  const isActive = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));

  return (
    <Link
      className={`px-3 py-1.5 text-sm font-medium transition ${
        isActive ? "text-cyan-300" : "text-slate-400 hover:text-slate-200"
      }`}
      href={href}
    >
      {children}
    </Link>
  );
}
