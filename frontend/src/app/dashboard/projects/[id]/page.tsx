"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Project = {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

type Target = {
  id: string;
  project_id: string;
  value: string;
  kind: string;
  in_scope: boolean;
  created_at: string;
};

type Scan = {
  id: string;
  target_id: string;
  scan_type: "subdomain_enum" | "http_probe" | "port_scan";
  status: "pending" | "running" | "completed" | "failed";
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
};

type ScanResult = {
  id: string;
  scan_id: string;
  value: string;
  data: Record<string, unknown> | null;
  created_at: string;
};

type ScanType = Scan["scan_type"];

const scanLabels: Record<ScanType, string> = {
  subdomain_enum: "Subdomains",
  http_probe: "HTTP Probe",
  port_scan: "Port Scan",
};

const statusLabels: Record<Scan["status"], string> = {
  pending: "Pendente",
  running: "Rodando",
  completed: "Concluido",
  failed: "Falhou",
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

export default function ProjectDetail() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const [project, setProject] = useState<Project | null>(null);
  const [targets, setTargets] = useState<Target[]>([]);
  const [scansByTarget, setScansByTarget] = useState<Record<string, Scan[]>>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [startingScan, setStartingScan] = useState<string | null>(null);
  const [deletingTarget, setDeletingTarget] = useState<string | null>(null);
  const [selectedScan, setSelectedScan] = useState<Scan | null>(null);
  const [scanResults, setScanResults] = useState<ScanResult[]>([]);
  const [loadingResults, setLoadingResults] = useState(false);

  async function requestWithAuth(path: string, init: RequestInit = {}) {
    const token = getStoredToken();
    if (!token) {
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

  async function loadProject() {
    const projectResponse = await requestWithAuth(`/api/v1/projects/${projectId}`);
    if (!projectResponse) {
      return;
    }

    if (projectResponse.status === 404) {
      setError("Projeto nao encontrado.");
      return;
    }

    if (!projectResponse.ok) {
      throw new Error("project_failed");
    }

    const targetResponse = await requestWithAuth(
      `/api/v1/projects/${projectId}/targets`,
    );
    if (!targetResponse) {
      return;
    }

    if (!targetResponse.ok) {
      throw new Error("targets_failed");
    }

    const projectData = (await projectResponse.json()) as Project;
    const targetData = (await targetResponse.json()) as Target[];
    const scanEntries = await Promise.all(
      targetData.map(async (target) => {
        const scanResponse = await requestWithAuth(
          `/api/v1/targets/${target.id}/scans`,
        );

        if (!scanResponse || !scanResponse.ok) {
          return [target.id, []] as const;
        }

        const scans = (await scanResponse.json()) as Scan[];
        return [target.id, scans] as const;
      }),
    );

    setProject(projectData);
    setTargets(targetData);
    setScansByTarget(Object.fromEntries(scanEntries));
  }

  useEffect(() => {
    loadProject()
      .catch(() => setError("Nao foi possivel carregar o projeto."))
      .finally(() => setLoading(false));
  }, [projectId]);

  async function handleCreateTarget(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setCreating(true);

    const form = event.currentTarget;
    const formData = new FormData(form);
    const value = String(formData.get("value") ?? "").trim();
    const kind = String(formData.get("kind") ?? "domain");

    if (!value) {
      setError("Informe o target.");
      setCreating(false);
      return;
    }

    try {
      const response = await requestWithAuth(
        `/api/v1/projects/${projectId}/targets`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ value, kind }),
        },
      );

      if (!response) {
        return;
      }

      if (response.status === 409) {
        setError("Esse target ja existe no projeto.");
        return;
      }

      if (!response.ok) {
        throw new Error("create_target_failed");
      }

      const created = (await response.json()) as Target;
      setTargets((current) => [created, ...current]);
      setScansByTarget((current) => ({ ...current, [created.id]: [] }));
      form.reset();
    } catch {
      setError("Nao foi possivel criar o target.");
    } finally {
      setCreating(false);
    }
  }

  async function handleStartScan(targetId: string, scanType: ScanType) {
    setError("");
    setStartingScan(`${targetId}:${scanType}`);

    try {
      const response = await requestWithAuth(`/api/v1/targets/${targetId}/scans`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scan_type: scanType }),
      });

      if (!response) {
        return;
      }

      if (response.status === 422) {
        setError("Target fora de escopo.");
        return;
      }

      if (!response.ok) {
        throw new Error("start_scan_failed");
      }

      const created = (await response.json()) as Scan;
      setScansByTarget((current) => ({
        ...current,
        [targetId]: [created, ...(current[targetId] ?? [])],
      }));
    } catch {
      setError("Nao foi possivel iniciar o scan.");
    } finally {
      setStartingScan(null);
    }
  }

  async function handleDeleteTarget(targetId: string) {
    setError("");
    setDeletingTarget(targetId);

    try {
      const response = await requestWithAuth(
        `/api/v1/projects/${projectId}/targets/${targetId}`,
        { method: "DELETE" },
      );

      if (!response) {
        return;
      }

      if (!response.ok) {
        throw new Error("delete_target_failed");
      }

      setTargets((current) => current.filter((target) => target.id !== targetId));
      setScansByTarget((current) => {
        const next = { ...current };
        delete next[targetId];
        return next;
      });
      if (selectedScan?.target_id === targetId) {
        setSelectedScan(null);
        setScanResults([]);
      }
    } catch {
      setError("Nao foi possivel remover o target.");
    } finally {
      setDeletingTarget(null);
    }
  }

  async function handleLoadResults(scan: Scan) {
    setError("");
    setSelectedScan(scan);
    setLoadingResults(true);

    try {
      const response = await requestWithAuth(`/api/v1/scans/${scan.id}/results`);

      if (!response) {
        return;
      }

      if (!response.ok) {
        throw new Error("results_failed");
      }

      const results = (await response.json()) as ScanResult[];
      setScanResults(results);
    } catch {
      setError("Nao foi possivel carregar os resultados.");
    } finally {
      setLoadingResults(false);
    }
  }

  function handleLogout() {
    clearStoredToken();
    window.location.href = "/";
  }

  function renderResultData(result: ScanResult, scanType: ScanType) {
    if (scanType === "subdomain_enum") {
      return <p className="text-sm font-medium text-white">{result.value}</p>;
    }

    if (scanType === "http_probe") {
      return (
        <div className="grid gap-1">
          <p className="break-all text-sm font-medium text-white">{result.value}</p>
          <p className="text-xs text-slate-400">
            Status: {String(result.data?.status_code ?? "-")} | Titulo:{" "}
            {String(result.data?.title ?? "-")}
          </p>
          {Array.isArray(result.data?.technologies) ? (
            <p className="text-xs text-slate-400">
              Tecnologias: {result.data.technologies.join(", ") || "-"}
            </p>
          ) : null}
        </div>
      );
    }

    return (
      <div className="grid gap-1">
        <p className="text-sm font-medium text-white">{result.value}</p>
        <p className="text-xs text-slate-400">
          Porta: {String(result.data?.port ?? "-")} | Servico:{" "}
          {String(result.data?.service ?? "-")} | Estado:{" "}
          {String(result.data?.state ?? "-")}
        </p>
        {result.data?.version ? (
          <p className="text-xs text-slate-400">
            Versao: {String(result.data.version)}
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[#06111f] text-slate-100">
      <header className="border-b border-white/10 bg-[#071827] px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
          <Link href="/dashboard">
            <img
              alt="Clavis"
              className="h-auto w-32"
              height="105"
              src="/clavis-logo.svg"
              width="301"
            />
          </Link>
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
            <Link className="text-sm font-medium text-cyan-200" href="/dashboard">
              Voltar para projetos
            </Link>
            <h1 className="mt-3 text-3xl font-semibold text-white">
              {project ? project.name : "Projeto"}
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              {project?.description || "Gerencie targets e scans deste projeto."}
            </p>
          </div>
          <div className="grid grid-cols-2 border border-white/10 bg-[#0a1f35]">
            <div className="border-r border-white/10 px-5 py-3">
              <p className="text-xs uppercase text-slate-400">Targets</p>
              <p className="mt-1 text-2xl font-semibold text-white">{targets.length}</p>
            </div>
            <div className="px-5 py-3">
              <p className="text-xs uppercase text-slate-400">In scope</p>
              <p className="mt-1 text-2xl font-semibold text-white">
                {targets.filter((target) => target.in_scope).length}
              </p>
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
          <form
            className="grid content-start gap-4 border border-white/10 bg-[#0a1f35] p-5"
            onSubmit={handleCreateTarget}
          >
            <div>
              <h2 className="text-lg font-semibold text-white">Novo target</h2>
            </div>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-slate-200">Target</span>
              <input
                className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
                name="value"
                placeholder="clavis.com.br"
                type="text"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-slate-200">Tipo</span>
              <select
                className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
                defaultValue="domain"
                name="kind"
              >
                <option value="domain">Dominio</option>
                <option value="ip">IP</option>
              </select>
            </label>

            {error ? (
              <p className="border border-red-400/30 bg-red-400/10 px-3 py-2 text-sm text-red-200">
                {error}
              </p>
            ) : null}

            <button
              className="h-11 border border-cyan-300 bg-cyan-300 px-4 text-sm font-semibold text-[#06111f] disabled:cursor-not-allowed disabled:opacity-60"
              disabled={creating || loading}
              type="submit"
            >
              {creating ? "Adicionando..." : "Adicionar target"}
            </button>
          </form>

          <section className="border border-white/10 bg-[#0a1f35]">
            <div className="border-b border-white/10 px-5 py-4">
              <h2 className="text-lg font-semibold text-white">Targets</h2>
            </div>

            {loading ? (
              <div className="px-5 py-10 text-sm text-slate-400">Carregando targets...</div>
            ) : targets.length === 0 ? (
              <div className="px-5 py-10 text-sm text-slate-400">
                Nenhum target criado ainda.
              </div>
            ) : (
              <div className="divide-y divide-white/10">
                {targets.map((target) => (
                  <article
                    className="grid gap-4 px-5 py-4"
                    key={target.id}
                  >
                    <div className="grid gap-3 md:grid-cols-[1fr_auto] md:items-center">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="truncate text-base font-semibold text-white">
                            {target.value}
                          </h3>
                          <span className="border border-cyan-300/30 px-2 py-1 text-xs uppercase text-cyan-200">
                            {target.kind}
                          </span>
                          <span className="border border-white/10 px-2 py-1 text-xs uppercase text-slate-300">
                            {target.in_scope ? "In scope" : "Out of scope"}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 md:justify-end">
                        <div className="text-left text-xs uppercase text-slate-500 md:text-right">
                          <p>Criado em</p>
                          <p className="mt-1 font-semibold text-slate-300">
                            {formatDate(target.created_at)}
                          </p>
                        </div>
                        <button
                          className="h-9 border border-red-300/30 px-3 text-xs font-semibold uppercase text-red-200 transition hover:border-red-300 disabled:cursor-not-allowed disabled:opacity-50"
                          disabled={deletingTarget === target.id}
                          onClick={() => handleDeleteTarget(target.id)}
                          type="button"
                        >
                          {deletingTarget === target.id ? "Removendo..." : "Remover"}
                        </button>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {(Object.keys(scanLabels) as ScanType[]).map((scanType) => (
                        <button
                          className="h-9 border border-cyan-300/40 px-3 text-xs font-semibold uppercase text-cyan-100 transition hover:border-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
                          disabled={
                            !target.in_scope ||
                            startingScan === `${target.id}:${scanType}`
                          }
                          key={scanType}
                          onClick={() => handleStartScan(target.id, scanType)}
                          type="button"
                        >
                          {startingScan === `${target.id}:${scanType}`
                            ? "Iniciando..."
                            : scanLabels[scanType]}
                        </button>
                      ))}
                    </div>

                    {(scansByTarget[target.id] ?? []).length > 0 ? (
                      <div className="border border-white/10">
                        {(scansByTarget[target.id] ?? []).slice(0, 3).map((scan) => (
                          <div
                            className="grid gap-2 border-b border-white/10 px-3 py-2 last:border-b-0 md:grid-cols-[1fr_auto] md:items-center"
                            key={scan.id}
                          >
                            <div className="min-w-0">
                              <p className="truncate text-sm font-medium text-slate-200">
                                {scanLabels[scan.scan_type]}
                              </p>
                              {scan.error ? (
                                <p className="mt-1 truncate text-xs text-red-200">
                                  {scan.error}
                                </p>
                              ) : null}
                            </div>
                            <div className="flex items-center gap-3 text-xs uppercase text-slate-400 md:justify-end">
                              <span className="text-slate-300">
                                {statusLabels[scan.status]}
                              </span>
                              <span>{formatDate(scan.created_at)}</span>
                              <button
                                className="font-semibold text-cyan-200 transition hover:text-cyan-100"
                                onClick={() => handleLoadResults(scan)}
                                type="button"
                              >
                                Resultados
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>

        {selectedScan ? (
          <section className="border border-white/10 bg-[#0a1f35]">
            <div className="grid gap-2 border-b border-white/10 px-5 py-4 md:grid-cols-[1fr_auto] md:items-center">
              <div>
                <p className="text-xs font-semibold uppercase text-cyan-200">
                  Resultados
                </p>
                <h2 className="mt-1 text-lg font-semibold text-white">
                  {scanLabels[selectedScan.scan_type]} -{" "}
                  {statusLabels[selectedScan.status]}
                </h2>
              </div>
              <button
                className="h-9 border border-white/15 px-3 text-xs font-semibold uppercase text-slate-200 transition hover:border-cyan-300 hover:text-cyan-200"
                onClick={() => handleLoadResults(selectedScan)}
                type="button"
              >
                Atualizar
              </button>
            </div>

            {loadingResults ? (
              <div className="px-5 py-8 text-sm text-slate-400">
                Carregando resultados...
              </div>
            ) : scanResults.length === 0 ? (
              <div className="px-5 py-8 text-sm text-slate-400">
                Nenhum resultado encontrado para este scan.
              </div>
            ) : (
              <div className="divide-y divide-white/10">
                {scanResults.map((result) => (
                  <article className="px-5 py-4" key={result.id}>
                    {renderResultData(result, selectedScan.scan_type)}
                  </article>
                ))}
              </div>
            )}
          </section>
        ) : null}
      </section>
    </main>
  );
}
