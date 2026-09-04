"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import {
  apiFetch,
  CurrentUser,
  fetchCurrentUser,
  formatDate,
} from "@/lib/auth";

type ApiKey = {
  id: string;
  name: string;
  prefix: string;
  revoked: boolean;
  last_used_at: string | null;
  created_at: string;
};

type ApiKeyCreated = {
  id: string;
  name: string;
  prefix: string;
  raw_key: string;
  created_at: string;
};


export default function ApiKeysPage() {
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [newKey, setNewKey] = useState<ApiKeyCreated | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [confirmRevokeId, setConfirmRevokeId] = useState<string | null>(null);

  useEffect(() => {
    fetchCurrentUser().then((user) => {
      if (!user) {
        window.location.href = "/";
        return;
      }
      setCurrentUser(user);
    }).catch(() => {});
    loadKeys().finally(() => setLoading(false));
  }, []);

  async function loadKeys() {
    const response = await apiFetch("/auth/api-keys");
    if (!response) return;
    if (!response.ok) {
      setError("Nao foi possivel carregar as chaves.");
      return;
    }
    const data = (await response.json()) as ApiKey[];
    setKeys(data);
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNewKey(null);
    setCreating(true);

    const form = event.currentTarget;
    const formData = new FormData(form);
    const name = String(formData.get("name") ?? "").trim();

    if (!name) {
      setError("Informe um nome para a chave.");
      setCreating(false);
      return;
    }

    try {
      const response = await apiFetch("/auth/api-keys", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });

      if (!response) return;

      if (!response.ok) {
        throw new Error("create_failed");
      }

      const created = (await response.json()) as ApiKeyCreated;
      setNewKey(created);
      setKeys((current) => [
        {
          id: created.id,
          name: created.name,
          prefix: created.prefix,
          revoked: false,
          last_used_at: null,
          created_at: created.created_at,
        },
        ...current,
      ]);
      form.reset();
    } catch {
      setError("Nao foi possivel criar a chave.");
    } finally {
      setCreating(false);
    }
  }

  async function handleRevoke(keyId: string) {
    setError("");
    setRevokingId(keyId);
    setConfirmRevokeId(null);

    try {
      const response = await apiFetch(`/auth/api-keys/${keyId}`, {
        method: "DELETE",
      });

      if (!response) return;

      if (!response.ok) {
        throw new Error("revoke_failed");
      }

      setKeys((current) =>
        current.map((k) => (k.id === keyId ? { ...k, revoked: true } : k)),
      );
      if (newKey?.id === keyId) setNewKey(null);
    } catch {
      setError("Nao foi possivel revogar a chave.");
    } finally {
      setRevokingId(null);
    }
  }

  return (
    <main className="min-h-screen bg-[#06111f] text-slate-100">
      <AppHeader user={currentUser} />

      <section className="mx-auto grid max-w-6xl gap-6 px-6 py-8">
        <div>
          <p className="text-sm font-semibold uppercase text-cyan-200">Autenticacao</p>
          <h1 className="mt-2 text-3xl font-semibold text-white">API Keys</h1>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Chaves para autenticar a CLI e integrações externas. A chave completa é exibida
            apenas no momento da criação.
          </p>
        </div>

        {newKey ? (
          <div className="border border-cyan-300/30 bg-cyan-300/5 p-5">
            <p className="text-sm font-semibold text-cyan-200">
              Chave criada — copie agora
            </p>
            <p className="mt-1 text-xs text-slate-400">
              Esta é a única vez que a chave completa será exibida.
            </p>
            <div className="mt-3 flex items-center gap-3">
              <code className="flex-1 break-all rounded border border-white/10 bg-[#06111f] px-3 py-2 font-mono text-sm text-cyan-100">
                {newKey.raw_key}
              </code>
              <button
                className="shrink-0 border border-white/15 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-cyan-300 hover:text-cyan-200"
                onClick={() => navigator.clipboard.writeText(newKey.raw_key)}
                type="button"
              >
                Copiar
              </button>
            </div>
            <button
              className="mt-3 text-xs text-slate-500 hover:text-slate-400"
              onClick={() => setNewKey(null)}
              type="button"
            >
              Dispensar aviso
            </button>
          </div>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
          <form
            className="grid content-start gap-4 border border-white/10 bg-[#0a1f35] p-5"
            onSubmit={handleCreate}
          >
            <h2 className="text-lg font-semibold text-white">Nova chave</h2>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-slate-200">Nome</span>
              <input
                className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
                name="name"
                placeholder="CLI local, CI/CD..."
                type="text"
              />
            </label>

            {error ? (
              <p className="border border-red-400/30 bg-red-400/10 px-3 py-2 text-sm text-red-200">
                {error}
              </p>
            ) : null}

            <button
              className="h-11 border border-cyan-300 bg-cyan-300 px-4 text-sm font-semibold text-[#06111f] disabled:cursor-not-allowed disabled:opacity-60"
              disabled={creating}
              type="submit"
            >
              {creating ? "Criando..." : "Criar chave"}
            </button>
          </form>

          <section className="border border-white/10 bg-[#0a1f35]">
            <div className="border-b border-white/10 px-5 py-4">
              <h2 className="text-lg font-semibold text-white">Minhas chaves</h2>
            </div>

            {loading ? (
              <div className="px-5 py-10 text-sm text-slate-400">Carregando chaves...</div>
            ) : keys.length === 0 ? (
              <div className="px-5 py-10 text-sm text-slate-400">
                Nenhuma chave criada ainda.
              </div>
            ) : (
              <div className="divide-y divide-white/10">
                {keys.map((key) => (
                  <div
                    className="grid gap-2 px-5 py-4 md:grid-cols-[1fr_auto] md:items-center"
                    key={key.id}
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium text-white">{key.name}</span>
                        {key.revoked ? (
                          <span className="border border-red-400/30 px-2 py-0.5 text-xs uppercase text-red-300">
                            Revogada
                          </span>
                        ) : (
                          <span className="border border-cyan-300/30 px-2 py-0.5 text-xs uppercase text-cyan-200">
                            Ativa
                          </span>
                        )}
                      </div>
                      <p className="mt-1 font-mono text-xs text-slate-500">
                        {key.prefix}***
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        Criada em {formatDate(key.created_at)}
                        {key.last_used_at
                          ? ` · Último uso ${formatDate(key.last_used_at)}`
                          : " · Nunca usada"}
                      </p>
                    </div>

                    {!key.revoked ? (
                      <div className="flex items-center gap-2">
                        {confirmRevokeId === key.id ? (
                          <>
                            <button
                              className="h-9 border border-red-300 px-3 text-xs font-semibold uppercase text-red-200 transition hover:bg-red-300/10 disabled:cursor-not-allowed disabled:opacity-50"
                              disabled={revokingId === key.id}
                              onClick={() => handleRevoke(key.id)}
                              type="button"
                            >
                              {revokingId === key.id ? "Revogando..." : "Confirmar"}
                            </button>
                            <button
                              className="h-9 border border-white/15 px-3 text-xs font-semibold uppercase text-slate-400 transition hover:border-white/30 hover:text-slate-200"
                              onClick={() => setConfirmRevokeId(null)}
                              type="button"
                            >
                              Cancelar
                            </button>
                          </>
                        ) : (
                          <button
                            className="h-9 border border-red-300/30 px-3 text-xs font-semibold uppercase text-red-200 transition hover:border-red-300 disabled:cursor-not-allowed disabled:opacity-50"
                            disabled={revokingId === key.id}
                            onClick={() => setConfirmRevokeId(key.id)}
                            type="button"
                          >
                            Revogar
                          </button>
                        )}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}
