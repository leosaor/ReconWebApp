"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { API_URL } from "@/lib/auth";

export default function Register() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email") ?? "").trim();
    const password = String(formData.get("password") ?? "");
    const confirmPassword = String(formData.get("confirm_password") ?? "");
    const fullNameRaw = String(formData.get("full_name") ?? "").trim();
    const full_name = fullNameRaw || null;

    if (password !== confirmPassword) {
      setError("As senhas nao coincidem.");
      setLoading(false);
      return;
    }

    if (password.length < 8) {
      setError("A senha deve ter pelo menos 8 caracteres.");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name }),
      });

      if (response.status === 409) {
        setError("Email ja cadastrado.");
        return;
      }

      if (!response.ok) {
        const body = await response.json().catch(() => ({})) as { detail?: string };
        setError(body.detail ?? "Erro ao criar conta.");
        return;
      }

      setSuccess(true);
    } catch {
      setError("Nao foi possivel conectar ao servidor.");
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#06111f] px-6 py-10 text-slate-100">
        <section className="w-full max-w-md border border-white/10 bg-[#0a1f35] p-6 shadow-2xl shadow-black/20">
          <div className="mb-8">
            <img alt="Clavis" className="h-auto w-36" height="105" src="/clavis-logo.svg" width="301" />
          </div>
          <div className="mb-8">
            <h1 className="text-2xl font-semibold text-white">Conta criada</h1>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Sua conta foi criada com sucesso. Entre para comecar.
            </p>
          </div>
          <Link
            className="flex h-11 items-center justify-center border border-cyan-300 bg-cyan-300 px-4 text-sm font-semibold text-[#06111f]"
            href="/"
          >
            Ir para login
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#06111f] px-6 py-10 text-slate-100">
      <section className="w-full max-w-md border border-white/10 bg-[#0a1f35] p-6 shadow-2xl shadow-black/20">
        <div className="mb-8">
          <img alt="Clavis" className="h-auto w-36" height="105" src="/clavis-logo.svg" width="301" />
        </div>

        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-white">Criar conta</h1>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Preencha os dados para criar sua conta.
          </p>
        </div>

        <form className="grid gap-5" onSubmit={handleSubmit}>
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-slate-200">Email</span>
            <input
              className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
              name="email"
              placeholder="seu@email.com"
              required
              type="email"
            />
          </label>

          <label className="grid gap-2 text-sm">
            <span className="font-medium text-slate-200">Nome completo (opcional)</span>
            <input
              className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
              name="full_name"
              placeholder="Seu nome"
              type="text"
            />
          </label>

          <label className="grid gap-2 text-sm">
            <span className="font-medium text-slate-200">Senha</span>
            <input
              className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
              name="password"
              placeholder="Minimo 8 caracteres"
              type="password"
            />
          </label>

          <label className="grid gap-2 text-sm">
            <span className="font-medium text-slate-200">Confirmar senha</span>
            <input
              className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
              name="confirm_password"
              placeholder="Repita a senha"
              type="password"
            />
          </label>

          {error ? (
            <p className="border border-red-400/30 bg-red-400/10 px-3 py-2 text-sm text-red-200">
              {error}
            </p>
          ) : null}

          <button
            className="h-11 border border-cyan-300 bg-cyan-300 px-4 text-sm font-semibold text-[#06111f] disabled:cursor-not-allowed disabled:opacity-60"
            disabled={loading}
            type="submit"
          >
            {loading ? "Criando conta..." : "Criar conta"}
          </button>

          <p className="text-center text-sm text-slate-400">
            Ja tem conta?{" "}
            <Link className="font-medium text-cyan-200 hover:text-cyan-100" href="/">
              Entrar
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}
