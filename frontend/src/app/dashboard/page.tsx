"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Project = {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

function getStoredToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return (
    window.localStorage.getItem("access_token") ??
    window.sessionStorage.getItem("access_token")
  );
}

function clearStoredToken() {
  window.localStorage.removeItem("access_token");
  window.sessionStorage.removeItem("access_token");
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const latestProject = useMemo(() => projects[0], [projects]);

  async function fetchProjects(token: string) {
    const response = await fetch(`${API_URL}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.status === 401 || response.status === 403) {
      clearStoredToken();
      window.location.href = "/";
      return;
    }

    if (!response.ok) {
      throw new Error("projects_failed");
    }

    const data = (await response.json()) as Project[];
    setProjects(data);
  }

  useEffect(() => {
    const token = getStoredToken();

    if (!token) {
      window.location.href = "/";
      return;
    }

    fetchProjects(token)
      .catch(() => setError("Nao foi possivel carregar os projetos."))
      .finally(() => setLoading(false));
  }, []);

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setCreating(true);

    const token = getStoredToken();
    if (!token) {
      window.location.href = "/";
      return;
    }

    const form = event.currentTarget;
    const formData = new FormData(form);
    const name = String(formData.get("name") ?? "").trim();
    const description = String(formData.get("description") ?? "").trim();

    if (!name) {
      setError("Informe o nome do projeto.");
      setCreating(false);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/v1/projects`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          description: description || null,
        }),
      });

      if (response.status === 401 || response.status === 403) {
        clearStoredToken();
        window.location.href = "/";
        return;
      }

      if (!response.ok) {
        throw new Error("create_failed");
      }

      const created = (await response.json()) as Project;
      setProjects((current) => [created, ...current]);
      form.reset();
    } catch {
      setError("Nao foi possivel criar o projeto.");
    } finally {
      setCreating(false);
    }
  }

  function handleLogout() {
    clearStoredToken();
    window.location.href = "/";
  }

  return (
    <main className="min-h-screen bg-[#06111f] text-slate-100">
      <header className="border-b border-white/10 bg-[#071827] px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
          <img
            alt="Clavis"
            className="h-auto w-32"
            height="105"
            src="/clavis-logo.svg"
            width="301"
          />
          <button
            className="h-10 border border-white/15 px-4 text-sm font-medium text-slate-200 transition hover:border-cyan-300 hover:text-cyan-200"
            onClick={handleLogout}
            type="button"
          >
            Sair
          </button>
        </div>
      </header>

      <section className="mx-auto grid max-w-6xl gap-6 px-6 py-8">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <p className="text-sm font-semibold uppercase text-cyan-200">Recon Surface</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Projetos</h1>
          </div>
          <div className="grid grid-cols-2 border border-white/10 bg-[#0a1f35]">
            <div className="border-r border-white/10 px-5 py-3">
              <p className="text-xs uppercase text-slate-400">Projetos</p>
              <p className="mt-1 text-2xl font-semibold text-white">{projects.length}</p>
            </div>
            <div className="px-5 py-3">
              <p className="text-xs uppercase text-slate-400">Ultimo</p>
              <p className="mt-1 max-w-36 truncate text-sm font-medium text-white">
                {latestProject ? latestProject.name : "-"}
              </p>
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
          <form
            className="grid content-start gap-4 border border-white/10 bg-[#0a1f35] p-5"
            onSubmit={handleCreateProject}
          >
            <div>
              <h2 className="text-lg font-semibold text-white">Novo projeto</h2>
            </div>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-slate-200">Nome</span>
              <input
                className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
                name="name"
                placeholder="Cliente ou dominio"
                type="text"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-slate-200">Descricao</span>
              <textarea
                className="min-h-24 resize-none border border-white/10 bg-[#06111f] px-3 py-3 text-slate-100 outline-none transition focus:border-cyan-300"
                name="description"
                placeholder="Escopo inicial"
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
              {creating ? "Criando..." : "Criar projeto"}
            </button>
          </form>

          <section className="border border-white/10 bg-[#0a1f35]">
            <div className="border-b border-white/10 px-5 py-4">
              <h2 className="text-lg font-semibold text-white">Projetos ativos</h2>
            </div>

            {loading ? (
              <div className="px-5 py-10 text-sm text-slate-400">Carregando projetos...</div>
            ) : projects.length === 0 ? (
              <div className="px-5 py-10 text-sm text-slate-400">
                Nenhum projeto criado ainda.
              </div>
            ) : (
              <div className="divide-y divide-white/10">
                {projects.map((project) => (
                  <Link
                    className="grid gap-3 px-5 py-4 transition hover:bg-white/[0.03] md:grid-cols-[1fr_auto] md:items-center"
                    href={`/dashboard/projects/${project.id}`}
                    key={project.id}
                  >
                    <div className="min-w-0">
                      <h3 className="truncate text-base font-semibold text-white">
                        {project.name}
                      </h3>
                      <p className="mt-1 line-clamp-2 text-sm leading-6 text-slate-400">
                        {project.description || "Sem descricao"}
                      </p>
                    </div>
                    <div className="text-left text-xs uppercase text-slate-500 md:text-right">
                      <p>Criado em</p>
                      <p className="mt-1 font-semibold text-slate-300">
                        {formatDate(project.created_at)}
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}
