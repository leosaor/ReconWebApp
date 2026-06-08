"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AppHeader } from "@/components/AppHeader";
import {
  API_URL,
  clearStoredToken,
  CurrentUser,
  fetchCurrentUser,
  formatDate,
  getStoredToken,
} from "@/lib/auth";

type Project = {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export default function Dashboard() {
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<Project | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const latestProject = useMemo(() => projects[0], [projects]);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      window.location.href = "/";
      return;
    }

    fetchCurrentUser().then(setCurrentUser).catch(() => {});
    fetchProjects(token)
      .catch(() => setError("Nao foi possivel carregar os projetos."))
      .finally(() => setLoading(false));
  }, []);

  async function fetchProjects(token: string) {
    const response = await fetch(`${API_URL}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.status === 401 || response.status === 403) {
      clearStoredToken();
      window.location.href = "/";
      return;
    }

    if (!response.ok) throw new Error("projects_failed");

    const data = (await response.json()) as Project[];
    setProjects(data);
  }

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
        body: JSON.stringify({ name, description: description || null }),
      });

      if (response.status === 401 || response.status === 403) {
        clearStoredToken();
        window.location.href = "/";
        return;
      }

      if (!response.ok) throw new Error("create_failed");

      const created = (await response.json()) as Project;
      setProjects((current) => [created, ...current]);
      form.reset();
    } catch {
      setError("Nao foi possivel criar o projeto.");
    } finally {
      setCreating(false);
    }
  }

  async function handleDeleteConfirm() {
    if (!confirmDelete) return;
    const token = getStoredToken();
    if (!token) return;

    setDeleting(confirmDelete.id);
    setConfirmDelete(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/projects/${confirmDelete.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.status === 401 || response.status === 403) {
        clearStoredToken();
        window.location.href = "/";
        return;
      }

      if (!response.ok) throw new Error("delete_failed");

      setProjects((current) => current.filter((p) => p.id !== confirmDelete.id));
    } catch {
      setError("Nao foi possivel excluir o projeto.");
    } finally {
      setDeleting(null);
    }
  }

  return (
    <main className="min-h-screen bg-[#06111f] text-slate-100">
      <AppHeader user={currentUser} />

      {confirmDelete ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div className="w-full max-w-md border border-white/10 bg-[#0a1f35] p-6">
            <h3 className="text-base font-semibold text-white">Excluir projeto?</h3>
            <p className="mt-2 text-sm text-slate-400">
              Tem certeza que deseja excluir{" "}
              <span className="font-semibold text-white">{confirmDelete.name}</span>?
              Todos os targets e scans associados serao permanentemente removidos.
            </p>
            <div className="mt-5 flex justify-end gap-3">
              <button
                className="h-9 border border-white/10 px-4 text-sm text-slate-300 hover:bg-white/5"
                onClick={() => setConfirmDelete(null)}
              >
                Cancelar
              </button>
              <button
                className="h-9 border border-red-500 bg-red-500/10 px-4 text-sm font-semibold text-red-300 hover:bg-red-500/20"
                onClick={handleDeleteConfirm}
              >
                Excluir projeto
              </button>
            </div>
          </div>
        </div>
      ) : null}

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
                  <div key={project.id} className="grid md:grid-cols-[1fr_auto] md:items-center">
                    <Link
                      className="grid gap-3 px-5 py-4 transition hover:bg-white/[0.03] md:grid-cols-[1fr_auto] md:items-center"
                      href={`/dashboard/projects/${project.id}`}
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
                    <div className="px-4">
                      <button
                        className="h-8 border border-red-500/30 px-3 text-xs font-semibold text-red-400 transition hover:border-red-500 hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-40"
                        disabled={deleting === project.id}
                        onClick={() => setConfirmDelete(project)}
                      >
                        {deleting === project.id ? "Excluindo..." : "Excluir"}
                      </button>
                    </div>
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
