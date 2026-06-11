"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import {
  API_URL,
  clearStoredToken,
  CurrentUser,
  fetchCurrentUser,
  formatDate,
  getStoredToken,
} from "@/lib/auth";

type UserRole = "admin" | "pentester" | "viewer";

type AppUser = {
  id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
};

const roleLabels: Record<UserRole, string> = {
  admin: "Admin",
  pentester: "Pentester",
  viewer: "Viewer",
};

async function requestWithAuth(path: string, init: RequestInit = {}): Promise<Response | null> {
  const token = getStoredToken();
  if (!token) {
    clearStoredToken();
    window.location.href = "/";
    return null;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init.headers ?? {}),
    },
  });

  if (response.status === 401 || response.status === 403) {
    clearStoredToken();
    window.location.href = "/";
    return null;
  }

  return response;
}

export default function AdminPage() {
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [users, setUsers] = useState<AppUser[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      window.location.href = "/";
      return;
    }

    fetchCurrentUser().then(setCurrentUser).catch(() => {});
    loadUsers();
  }, []);

  async function loadUsers() {
    try {
      const response = await requestWithAuth("/users");
      if (!response) return;
      if (!response.ok) {
        setError("Nao foi possivel carregar os usuarios.");
        return;
      }
      const data = (await response.json()) as AppUser[];
      setUsers(data);
    } catch {
      setError("Nao foi possivel carregar os usuarios.");
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleActive(user: AppUser) {
    setError("");
    setUpdatingId(user.id);

    try {
      const response = await requestWithAuth(`/users/${user.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !user.is_active }),
      });

      if (!response) return;

      if (!response.ok) {
        throw new Error("update_failed");
      }

      const updated = (await response.json()) as AppUser;
      setUsers((current) => current.map((u) => (u.id === updated.id ? updated : u)));
    } catch {
      setError("Nao foi possivel atualizar o usuario.");
    } finally {
      setUpdatingId(null);
    }
  }

  async function handleChangeRole(user: AppUser, role: UserRole) {
    setError("");
    setUpdatingId(user.id);

    try {
      const shouldActivate = !user.is_active && role !== "viewer";
      const response = await requestWithAuth(`/users/${user.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role, ...(shouldActivate ? { is_active: true } : {}) }),
      });

      if (!response) return;

      if (!response.ok) {
        throw new Error("update_failed");
      }

      const updated = (await response.json()) as AppUser;
      setUsers((current) => current.map((u) => (u.id === updated.id ? updated : u)));
    } catch {
      setError("Nao foi possivel atualizar o usuario.");
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <main className="min-h-screen bg-[#06111f] text-slate-100">
      <AppHeader user={currentUser} />

      <section className="mx-auto grid max-w-6xl gap-6 px-6 py-8">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <p className="text-sm font-semibold uppercase text-cyan-200">Administracao</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Usuarios</h1>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Gerencie contas, roles e status de acesso.
            </p>
          </div>
          <div className="border border-white/10 bg-[#0a1f35] px-5 py-3">
            <p className="text-xs uppercase text-slate-400">Total</p>
            <p className="mt-1 text-2xl font-semibold text-white">{users.length}</p>
          </div>
        </div>

        {error ? (
          <p className="border border-red-400/30 bg-red-400/10 px-3 py-2 text-sm text-red-200">
            {error}
          </p>
        ) : null}

        <section className="border border-white/10 bg-[#0a1f35]">
          <div className="border-b border-white/10 px-5 py-4">
            <h2 className="text-lg font-semibold text-white">Lista de usuarios</h2>
          </div>

          {loading ? (
            <div className="px-5 py-10 text-sm text-slate-400">Carregando usuarios...</div>
          ) : users.length === 0 ? (
            <div className="px-5 py-10 text-sm text-slate-400">Nenhum usuario encontrado.</div>
          ) : (
            <div className="divide-y divide-white/10">
              {users.map((user) => (
                <div
                  className="grid gap-3 px-5 py-4 md:grid-cols-[1fr_auto] md:items-center"
                  key={user.id}
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-white">
                        {user.full_name ?? user.email}
                      </span>
                      {user.full_name ? (
                        <span className="text-sm text-slate-400">{user.email}</span>
                      ) : null}
                      <span
                        className={`border px-2 py-0.5 text-xs uppercase ${
                          user.is_active
                            ? "border-cyan-300/30 text-cyan-200"
                            : "border-red-400/30 text-red-300"
                        }`}
                      >
                        {user.is_active ? "Ativo" : "Inativo"}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      Criado em {formatDate(user.created_at)}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <select
                      className="h-9 border border-white/10 bg-[#06111f] px-2 text-xs font-semibold uppercase text-slate-200 outline-none transition focus:border-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={updatingId === user.id || user.id === currentUser?.id}
                      onChange={(e) => handleChangeRole(user, e.target.value as UserRole)}
                      value={user.role}
                    >
                      {(Object.keys(roleLabels) as UserRole[]).map((role) => (
                        <option key={role} value={role}>
                          {roleLabels[role]}
                        </option>
                      ))}
                    </select>

                    <button
                      className={`h-9 border px-3 text-xs font-semibold uppercase transition disabled:cursor-not-allowed disabled:opacity-50 ${
                        user.is_active
                          ? "border-red-300/30 text-red-200 hover:border-red-300"
                          : "border-cyan-300/30 text-cyan-200 hover:border-cyan-300"
                      }`}
                      disabled={updatingId === user.id || user.id === currentUser?.id}
                      onClick={() => handleToggleActive(user)}
                      type="button"
                    >
                      {updatingId === user.id
                        ? "Salvando..."
                        : user.is_active
                        ? "Desativar"
                        : "Ativar"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
