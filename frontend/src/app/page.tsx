"use client";

import { FormEvent, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    const formData = new FormData(event.currentTarget);
    const keepConnected = formData.get("remember") === "on";
    const storage = keepConnected ? window.localStorage : window.sessionStorage;

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          identifier: formData.get("username"),
          password: formData.get("password"),
        }),
      });

      if (!response.ok) {
        setError("Usuario ou senha invalidos.");
        return;
      }

      const data = (await response.json()) as { access_token: string };
      storage.setItem("access_token", data.access_token);
      window.location.href = "/dashboard";
    } catch {
      setError("Nao foi possivel conectar ao servidor.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#06111f] px-6 py-10 text-slate-100">
      <section className="w-full max-w-md border border-white/10 bg-[#0a1f35] p-6 shadow-2xl shadow-black/20">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center border border-cyan-300/60 bg-cyan-300 text-sm font-black text-[#06111f]">
            C
          </div>
          <div>
            <p className="text-lg font-semibold uppercase">clavis</p>
            <p className="text-xs uppercase text-cyan-200/70">Recon Surface</p>
          </div>
        </div>

        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-white">Entrar na plataforma</h1>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Acesso restrito para usuarios autorizados.
          </p>
        </div>

        <form className="grid gap-5" onSubmit={handleSubmit}>
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-slate-200">Usuario</span>
            <input
              className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
              name="username"
              placeholder="Digite seu usuario"
              type="text"
            />
          </label>

          <label className="grid gap-2 text-sm">
            <span className="font-medium text-slate-200">Senha</span>
            <input
              className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
              name="password"
              placeholder="Digite sua senha"
              type="password"
            />
          </label>

          <div className="text-sm">
            <label className="flex items-center gap-2 text-slate-300">
              <input className="h-4 w-4 accent-cyan-300" name="remember" type="checkbox" />
              Manter conectado
            </label>
          </div>

          {error ? (
            <p className="border border-red-400/30 bg-red-400/10 px-3 py-2 text-sm text-red-200">
              {error}
            </p>
          ) : null}

          <button
            className="h-11 border border-cyan-300 bg-cyan-300 px-4 text-sm font-semibold text-[#06111f]"
            disabled={loading}
            type="submit"
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </section>
    </main>
  );
}
