"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
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
  owner_name: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

type Target = {
  id: string;
  project_id: string;
  value: string;
  created_at: string;
};

type ScanType = "subdomain_enum" | "http_probe" | "port_scan" | "header_check" | "clickjacking" | "domain_spoofing" | "tls_scan" | "content_fuzz" | "git_dump" | "nuclei_scan";

type Scan = {
  id: string;
  target_id: string;
  scan_type: ScanType;
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

type RunnableModule = "subdomain_enum" | "http_probe" | "port_scan" | "header_check" | "clickjacking" | "domain_spoofing" | "tls_scan" | "content_fuzz" | "git_dump" | "nuclei_scan";

const MODULE_OPTIONS: { type: RunnableModule; label: string; description: string }[] = [
  { type: "subdomain_enum", label: "Subdomain Enum", description: "Enumera subdomínios via subfinder" },
  { type: "http_probe", label: "HTTP Probe", description: "Httpx nos subdominios" },
  { type: "content_fuzz", label: "Fuzzing", description: "Feroxbuster com Wordlist common" },
  { type: "nuclei_scan", label: "Nuclei", description: "Roda Nuclei no target original" },
  { type: "port_scan", label: "Port Scan", description: "Nmap nos hosts que respondem 200 no httpx" },
  { type: "git_dump", label: "Git Dumper", description: "Testa exposicao de .git em URLs HTTP 200" },
  { type: "header_check", label: "Cabeçalhos HTTP", description: "shcheck" },
  { type: "clickjacking", label: "Clickjacking", description: "Teste de ClickJacking" },
  { type: "tls_scan", label: "TLS/Cifras", description: "sslscan para testes de TLS e cifras" },
  { type: "domain_spoofing", label: "Domain Spoofing", description: "SPF e DMARC via DNS" },
];

function createEmptyModuleSelection(): Record<RunnableModule, boolean> {
  return {
    subdomain_enum: false,
    http_probe: false,
    content_fuzz: false,
    nuclei_scan: false,
    port_scan: false,
    git_dump: false,
    header_check: false,
    clickjacking: false,
    tls_scan: false,
    domain_spoofing: false,
  };
}

const scanLabels: Record<ScanType, string> = {
  subdomain_enum: "Subdomain Enum",
  http_probe: "HTTP Probe",
  port_scan: "Port Scan",
  header_check: "Cabeçalhos HTTP",
  clickjacking: "Clickjacking",
  domain_spoofing: "Domain Spoofing",
  tls_scan: "TLS/Cifras",
  content_fuzz: "Fuzzing",
  git_dump: "Git Dumper",
  nuclei_scan: "Nuclei",
};

const statusLabels: Record<Scan["status"], string> = {
  pending: "Pendente",
  running: "Rodando",
  completed: "Concluido",
  failed: "Falhou",
};

const statusColors: Record<Scan["status"], string> = {
  pending: "text-yellow-300",
  running: "text-cyan-300",
  completed: "text-green-300",
  failed: "text-red-300",
};

const FUZZING_HIDDEN_EXTENSIONS = new Set(["css", "gif", "jpeg", "jpg", "png", "svf", "svg"]);

function isActiveStatus(status: Scan["status"]): boolean {
  return status === "pending" || status === "running";
}

function shouldShowFuzzingResult(result: ScanResult): boolean {
  const rawUrl = String(result.data?.url ?? result.value ?? "");
  const path = (() => {
    try {
      return new URL(rawUrl).pathname;
    } catch {
      return rawUrl.split("?")[0].split("#")[0];
    }
  })();
  const fileName = path.split("/").pop() ?? "";
  const extension = fileName.includes(".") ? fileName.split(".").pop()?.toLowerCase() : "";
  return !extension || !FUZZING_HIDDEN_EXTENSIONS.has(extension);
}

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

export default function ProjectDetail() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;

  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [targets, setTargets] = useState<Target[]>([]);
  const [scansByTarget, setScansByTarget] = useState<Record<string, Scan[]>>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [confirmDeleteTarget, setConfirmDeleteTarget] = useState<string | null>(null);
  const [deletingTarget, setDeletingTarget] = useState<string | null>(null);
  const [selectedScan, setSelectedScan] = useState<Scan | null>(null);
  const [scanResults, setScanResults] = useState<ScanResult[]>([]);
  const [loadingResults, setLoadingResults] = useState(false);
  const [downloadingArtifact, setDownloadingArtifact] = useState(false);

  const [executeModal, setExecuteModal] = useState<{ targetId: string; targetValue: string } | null>(null);
  const [modalModules, setModalModules] = useState<Record<RunnableModule, boolean>>(
    createEmptyModuleSelection,
  );
  const [executingTarget, setExecutingTarget] = useState<string | null>(null);
  const [executingPhase, setExecutingPhase] = useState<string | null>(null);

  const scansByTargetRef = useRef(scansByTarget);
  useEffect(() => {
    scansByTargetRef.current = scansByTarget;
  }, [scansByTarget]);

  const selectedScanRef = useRef(selectedScan);
  useEffect(() => {
    selectedScanRef.current = selectedScan;
  }, [selectedScan]);

  useEffect(() => {
    fetchCurrentUser().then(setCurrentUser).catch(() => {});
    loadProject()
      .catch(() => setError("Nao foi possivel carregar o projeto."))
      .finally(() => setLoading(false));
  }, [projectId]);

  useEffect(() => {
    const activeScans = Object.values(scansByTarget)
      .flat()
      .filter((s) => isActiveStatus(s.status));

    if (activeScans.length === 0) return;

    const intervalId = setInterval(() => {
      const token = getStoredToken();
      if (!token) return;

      activeScans.forEach((scan) => {
        fetch(`${API_URL}/api/v1/scans/${scan.id}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
          .then((r) => (r.ok ? (r.json() as Promise<Scan>) : null))
          .then((updated) => {
            if (!updated) return;
            setScansByTarget((current) => ({
              ...current,
              [updated.target_id]: (current[updated.target_id] ?? []).map((s) =>
                s.id === updated.id ? updated : s,
              ),
            }));
            if (selectedScanRef.current?.id === updated.id) {
              setSelectedScan(updated);
            }
          })
          .catch(() => {});
      });
    }, 5000);

    return () => clearInterval(intervalId);
  }, [scansByTarget]);

  async function loadProject() {
    const projectResponse = await requestWithAuth(`/api/v1/projects/${projectId}`);
    if (!projectResponse) return;

    if (projectResponse.status === 404) {
      setError("Projeto nao encontrado.");
      return;
    }

    if (!projectResponse.ok) throw new Error("project_failed");

    const targetResponse = await requestWithAuth(`/api/v1/projects/${projectId}/targets`);
    if (!targetResponse || !targetResponse.ok) throw new Error("targets_failed");

    const projectData = (await projectResponse.json()) as Project;
    const targetData = (await targetResponse.json()) as Target[];
    const scanEntries = await Promise.all(
      targetData.map(async (target) => {
        const scanResponse = await requestWithAuth(`/api/v1/targets/${target.id}/scans`);
        if (!scanResponse || !scanResponse.ok) return [target.id, []] as const;
        const scans = (await scanResponse.json()) as Scan[];
        return [target.id, scans] as const;
      }),
    );

    setProject(projectData);
    setTargets(targetData);
    setScansByTarget(Object.fromEntries(scanEntries));
  }

  async function startOneScan(targetId: string, scanType: ScanType): Promise<Scan | null> {
    const response = await requestWithAuth(`/api/v1/targets/${targetId}/scans`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scan_type: scanType }),
    });
    if (!response || !response.ok) return null;
    const created = (await response.json()) as Scan;
    setScansByTarget((current) => ({
      ...current,
      [targetId]: [created, ...(current[targetId] ?? [])],
    }));
    return created;
  }

  function waitForScan(scanId: string, targetId: string): Promise<void> {
    return new Promise((resolve) => {
      const intervalId = setInterval(async () => {
        const token = getStoredToken();
        if (!token) {
          clearInterval(intervalId);
          resolve();
          return;
        }
        try {
          const r = await fetch(`${API_URL}/api/v1/scans/${scanId}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (!r.ok) {
            clearInterval(intervalId);
            resolve();
            return;
          }
          const updated = (await r.json()) as Scan;
          setScansByTarget((current) => ({
            ...current,
            [targetId]: (current[targetId] ?? []).map((s) =>
              s.id === scanId ? updated : s,
            ),
          }));
          if (!isActiveStatus(updated.status)) {
            clearInterval(intervalId);
            resolve();
          }
        } catch {
          clearInterval(intervalId);
          resolve();
        }
      }, 3000);
    });
  }

  function openExecuteModal(target: Target) {
    setExecuteModal({ targetId: target.id, targetValue: target.value });
    setModalModules(createEmptyModuleSelection());
  }

  async function handleExecuteConfirm() {
    if (!executeModal) return;
    const { targetId } = executeModal;

    const phases = MODULE_OPTIONS.filter((m) => modalModules[m.type]);
    if (phases.length === 0) return;

    setExecuteModal(null);
    setError("");
    setExecutingTarget(targetId);

    try {
      for (const phase of phases) {
        setExecutingPhase(phase.label);
        const scan = await startOneScan(targetId, phase.type);
        if (scan) await waitForScan(scan.id, targetId);
      }
    } catch {
      setError("Erro durante a execução dos módulos.");
    } finally {
      setExecutingTarget(null);
      setExecutingPhase(null);
    }
  }

  async function handleCreateTarget(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setCreating(true);

    const form = event.currentTarget;
    const formData = new FormData(form);
    const value = String(formData.get("value") ?? "").trim();

    if (!value) {
      setError("Informe o target.");
      setCreating(false);
      return;
    }

    try {
      const response = await requestWithAuth(`/api/v1/projects/${projectId}/targets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value, kind: "domain" }),
      });

      if (!response) return;

      if (response.status === 409) {
        setError("Esse target ja existe no projeto.");
        return;
      }

      if (!response.ok) throw new Error("create_target_failed");

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

  async function handleDeleteTarget(targetId: string) {
    setError("");
    setConfirmDeleteTarget(null);
    setDeletingTarget(targetId);

    try {
      const response = await requestWithAuth(
        `/api/v1/projects/${projectId}/targets/${targetId}`,
        { method: "DELETE" },
      );

      if (!response) return;
      if (!response.ok) throw new Error("delete_target_failed");

      setTargets((current) => current.filter((t) => t.id !== targetId));
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
      if (!response) return;
      if (!response.ok) throw new Error("results_failed");
      const results = (await response.json()) as ScanResult[];
      setScanResults(results);
    } catch {
      setError("Nao foi possivel carregar os resultados.");
    } finally {
      setLoadingResults(false);
    }
  }

  async function handleDownloadArtifact(scan: Scan) {
    setError("");
    setDownloadingArtifact(true);

    try {
      const response = await requestWithAuth(`/api/v1/scans/${scan.id}/artifact`);
      if (!response) return;
      if (!response.ok) throw new Error("artifact_failed");

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = scan.scan_type === "nuclei_scan"
        ? `nuclei-${scan.id}.txt`
        : `feroxbuster-${scan.id}.txt`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch {
      setError("Nao foi possivel baixar o arquivo do scan.");
    } finally {
      setDownloadingArtifact(false);
    }
  }

  function renderResultData(result: ScanResult, scanType: ScanType) {
    if (scanType === "subdomain_enum") {
      return <p className="text-sm font-medium text-white">{result.value}</p>;
    }

    if (scanType === "http_probe") {
      const location = result.data?.location as string | undefined;
      const hostIp = result.data?.host_ip as string | undefined;
      const dnsIps = Array.isArray(result.data?.a) ? (result.data.a as string[]) : [];
      const ips = hostIp ? [hostIp] : dnsIps;
      const cdnName = result.data?.cdn_name as string | undefined;
      const cdnType = result.data?.cdn_type as string | undefined;
      const hasCdn = Boolean(result.data?.cdn || cdnName || cdnType);
      const technologies = Array.isArray(result.data?.technologies)
        ? (result.data.technologies as string[])
        : Array.isArray(result.data?.tech)
          ? (result.data.tech as string[])
          : [];
      return (
        <div className="grid gap-1">
          <p className="break-all text-sm font-medium text-white">{result.value}</p>
          <p className="text-xs text-slate-400">
            Status: {String(result.data?.status_code ?? "-")} | Titulo:{" "}
            {String(result.data?.title ?? "-")}
          </p>
          {location ? (
            <p className="break-all text-xs text-slate-400">Redirect: {location}</p>
          ) : null}
          {ips.length > 0 ? (
            <p className="break-all text-xs text-slate-400">IP: {ips.join(", ")}</p>
          ) : null}
          {hasCdn ? (
            <p className="text-xs text-slate-400">
              CDN: {[cdnName, cdnType].filter(Boolean).join(" / ") || "detectado"}
            </p>
          ) : null}
          {technologies.length > 0 ? (
            <p className="text-xs text-slate-400">
              Tecnologias: {technologies.join(", ")}
            </p>
          ) : null}
        </div>
      );
    }

    if (scanType === "header_check") {
      const svgB64 = result.data?.svg_b64 as string | undefined;
      return (
        <div className="grid gap-2">
          <p className="break-all text-sm font-medium text-white">{result.value}</p>
          {svgB64 ? (
            <img
              src={`data:image/svg+xml;base64,${svgB64}`}
              alt="shcheck output"
              className="w-full rounded border border-white/10"
            />
          ) : (
            <p className="text-xs text-slate-400">Sem resultado</p>
          )}
        </div>
      );
    }

    if (scanType === "clickjacking") {
      const vulnerable = result.data?.vulnerable as boolean | undefined;
      const screenshotB64 = result.data?.screenshot_b64 as string | undefined;
      return (
        <div className="grid gap-2">
          <div className="flex items-center gap-2">
            <p className="break-all text-sm font-medium text-white">{result.value}</p>
            <span className={`text-xs font-semibold uppercase ${vulnerable ? "text-red-300" : "text-green-300"}`}>
              {vulnerable ? "Vulneravel" : "Protegido"}
            </span>
          </div>
          {screenshotB64 ? (
            <img
              src={`data:image/png;base64,${screenshotB64}`}
              alt="clickjacking screenshot"
              className="w-full rounded border border-white/10"
            />
          ) : (
            <div className="space-y-1">
              <p className="text-xs text-slate-400">
                X-Frame-Options: {String(result.data?.x_frame_options ?? "ausente")}
              </p>
              <p className="text-xs text-slate-400">
                CSP frame-ancestors: {String(result.data?.csp_frame_ancestors ?? "ausente")}
              </p>
            </div>
          )}
        </div>
      );
    }

    if (scanType === "tls_scan") {
      const svgB64 = result.data?.svg_b64 as string | undefined;
      const outputFile = result.data?.output_file as string | undefined;
      const returnCode = result.data?.return_code;
      return (
        <div className="grid gap-2">
          <div>
            <p className="break-all text-sm font-medium text-white">{result.value}</p>
            <p className="text-xs text-slate-400">
              Exit code: {String(returnCode ?? "-")}
              {outputFile ? ` | Arquivo: ${outputFile}` : ""}
            </p>
          </div>
          {svgB64 ? (
            <img
              src={`data:image/svg+xml;base64,${svgB64}`}
              alt="sslscan output"
              className="w-full rounded border border-white/10"
            />
          ) : (
            <p className="text-xs text-slate-400">Sem resultado</p>
          )}
        </div>
      );
    }

    if (scanType === "content_fuzz") {
      const statusCode = result.data?.status_code;
      const contentLength = result.data?.content_length;
      const words = result.data?.words;
      const lines = result.data?.lines;
      const redirect = result.data?.redirect as string | undefined;
      return (
        <div className="grid gap-1">
          <p className="break-all text-sm font-medium text-white">{result.value}</p>
          <p className="text-xs text-slate-400">
            Status: {String(statusCode ?? "-")} | Tamanho: {String(contentLength ?? "-")} | Palavras:{" "}
            {String(words ?? "-")} | Linhas: {String(lines ?? "-")}
          </p>
          {redirect ? (
            <p className="break-all text-xs text-slate-400">Redirect: {redirect}</p>
          ) : null}
        </div>
      );
    }

    if (scanType === "git_dump") {
      const vulnerable = Boolean(result.data?.vulnerable);
      const gitUrl = result.data?.git_url as string | undefined;
      const dumpDir = result.data?.dump_dir as string | undefined;
      const returnCode = result.data?.return_code;
      return (
        <div className="grid gap-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="break-all text-sm font-medium text-white">{result.value}</p>
            <span className={`text-xs font-semibold uppercase ${vulnerable ? "text-red-300" : "text-green-300"}`}>
              {vulnerable ? "Vulneravel" : "Nao vulneravel"}
            </span>
          </div>
          <p className="break-all text-xs text-slate-400">Testado: {gitUrl ?? `${result.value}/.git`}</p>
          <p className="text-xs text-slate-400">Exit code: {String(returnCode ?? "-")}</p>
          {dumpDir ? (
            <p className="break-all text-xs text-slate-400">Dump: {dumpDir}</p>
          ) : null}
        </div>
      );
    }

    if (scanType === "nuclei_scan") {
      const severity = String(result.data?.severity ?? "-").toLowerCase();
      const severityClass = severity === "critical"
        ? "text-red-300"
        : severity === "high"
          ? "text-orange-300"
          : severity === "medium"
            ? "text-yellow-300"
            : "text-cyan-300";
      const tags = Array.isArray(result.data?.tags)
        ? (result.data.tags as string[])
        : typeof result.data?.tags === "string"
          ? String(result.data.tags).split(",").map((tag) => tag.trim()).filter(Boolean)
          : [];
      const extracted = Array.isArray(result.data?.extracted_results)
        ? (result.data.extracted_results as unknown[]).map(String)
        : [];
      return (
        <div className="grid gap-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="break-all text-sm font-medium text-white">
              {String(result.data?.template_id ?? result.data?.name ?? result.value)}
            </p>
            <span className={`text-xs font-semibold uppercase ${severityClass}`}>
              {severity}
            </span>
          </div>
          <p className="break-all text-xs text-slate-400">URL: {String(result.data?.matched_at ?? result.value)}</p>
          <p className="break-all text-xs text-slate-400">Raw: {String(result.data?.raw ?? "-")}</p>
          {result.data?.matcher_name ? (
            <p className="text-xs text-slate-400">Matcher: {String(result.data.matcher_name)}</p>
          ) : null}
          {result.data?.description ? (
            <p className="text-xs text-slate-400">{String(result.data.description)}</p>
          ) : null}
          {tags.length > 0 ? (
            <p className="break-all text-xs text-slate-400">Tags: {tags.join(", ")}</p>
          ) : null}
          {extracted.length > 0 ? (
            <p className="break-all text-xs text-slate-400">Extraido: {extracted.join(", ")}</p>
          ) : null}
        </div>
      );
    }

    if (scanType === "domain_spoofing") {
      const svgB64 = result.data?.svg_b64 as string | undefined;
      return (
        <div className="grid gap-2">
          <p className="text-sm font-medium text-white">{result.value}</p>
          {svgB64 ? (
            <img
              src={`data:image/svg+xml;base64,${svgB64}`}
              alt={`${String(result.value)} DNS check`}
              className="w-full rounded border border-white/10"
            />
          ) : (
            <p className="text-xs text-slate-400">Sem resultado</p>
          )}
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
          <p className="text-xs text-slate-400">Versao: {String(result.data.version)}</p>
        ) : null}
      </div>
    );
  }

  const anyModuleSelected = Object.values(modalModules).some(Boolean);
  const visibleScanResults = selectedScan?.scan_type === "content_fuzz"
    ? scanResults.filter(shouldShowFuzzingResult)
    : scanResults;

  return (
    <main className="min-h-screen bg-[#06111f] text-slate-100">
      <AppHeader user={currentUser} />

      {/* Modal de seleção de módulos */}
      {executeModal ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) setExecuteModal(null);
          }}
        >
          <div className="w-full max-w-sm border border-white/10 bg-[#0a1f35] p-6 shadow-2xl">
            <h2 className="text-lg font-semibold text-white">Selecionar módulos</h2>
            <p className="mt-1 truncate text-sm text-slate-400">{executeModal.targetValue}</p>

            <div className="mt-5 grid gap-3">
              {MODULE_OPTIONS.map((module) => (
                <label
                  className="flex cursor-pointer items-start gap-3 rounded border border-white/10 p-3 transition hover:border-white/20"
                  key={module.type}
                >
                  <input
                    checked={modalModules[module.type]}
                    className="mt-0.5 h-4 w-4 accent-cyan-300"
                    onChange={(e) =>
                      setModalModules((prev) => ({ ...prev, [module.type]: e.target.checked }))
                    }
                    type="checkbox"
                  />
                  <div>
                    <p className="text-sm font-medium text-slate-100">{module.label}</p>
                    <p className="text-xs text-slate-400">{module.description}</p>
                  </div>
                </label>
              ))}
            </div>

            <div className="mt-6 flex gap-3">
              <button
                className="h-10 flex-1 border border-cyan-300 bg-cyan-300 px-4 text-sm font-semibold text-[#06111f] disabled:cursor-not-allowed disabled:opacity-50"
                disabled={!anyModuleSelected}
                onClick={handleExecuteConfirm}
                type="button"
              >
                Executar
              </button>
              <button
                className="h-10 border border-white/15 px-4 text-sm font-semibold text-slate-300 transition hover:border-white/30 hover:text-slate-100"
                onClick={() => setExecuteModal(null)}
                type="button"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      ) : null}

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
          <div className="border border-white/10 bg-[#0a1f35] px-5 py-3">
            <p className="text-xs uppercase text-slate-400">Targets</p>
            <p className="mt-1 text-2xl font-semibold text-white">{targets.length}</p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
          <form
            className="grid content-start gap-4 border border-white/10 bg-[#0a1f35] p-5"
            onSubmit={handleCreateTarget}
          >
            <h2 className="text-lg font-semibold text-white">Novo target</h2>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-slate-200">Target</span>
              <input
                className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
                name="value"
                placeholder="Domain or IP"
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
                  <article className="grid gap-4 px-5 py-4" key={target.id}>
                    <div className="grid gap-3 md:grid-cols-[1fr_auto] md:items-center">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="truncate text-base font-semibold text-white">
                            {target.value}
                          </h3>
                        </div>
                        {executingTarget === target.id && executingPhase ? (
                          <p className="mt-1 text-xs text-cyan-300">
                            {executingPhase}
                            <span className="ml-1 animate-pulse">•</span>
                          </p>
                        ) : null}
                      </div>
                      <div className="flex items-center gap-3 md:justify-end">
                        <div className="text-left text-xs uppercase text-slate-500 md:text-right">
                          <p>Criado em</p>
                          <p className="mt-1 font-semibold text-slate-300">
                            {formatDate(target.created_at)}
                          </p>
                        </div>

                        <button
                          className="h-9 border border-cyan-300/40 px-3 text-xs font-semibold uppercase text-cyan-100 transition hover:border-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
                          disabled={executingTarget === target.id}
                          onClick={() => openExecuteModal(target)}
                          title="Selecionar modulos e executar"
                          type="button"
                        >
                          {executingTarget === target.id ? "Rodando..." : "Executar"}
                        </button>

                        {confirmDeleteTarget === target.id ? (
                          <div className="flex items-center gap-2">
                            <button
                              className="h-9 border border-red-300 px-3 text-xs font-semibold uppercase text-red-200 transition hover:bg-red-300/10 disabled:cursor-not-allowed disabled:opacity-50"
                              disabled={deletingTarget === target.id}
                              onClick={() => handleDeleteTarget(target.id)}
                              type="button"
                            >
                              {deletingTarget === target.id ? "Removendo..." : "Confirmar"}
                            </button>
                            <button
                              className="h-9 border border-white/15 px-3 text-xs font-semibold uppercase text-slate-400 transition hover:border-white/30 hover:text-slate-200"
                              onClick={() => setConfirmDeleteTarget(null)}
                              type="button"
                            >
                              Cancelar
                            </button>
                          </div>
                        ) : (
                          <button
                            className="h-9 border border-red-300/30 px-3 text-xs font-semibold uppercase text-red-200 transition hover:border-red-300 disabled:cursor-not-allowed disabled:opacity-50"
                            disabled={deletingTarget === target.id}
                            onClick={() => setConfirmDeleteTarget(target.id)}
                            type="button"
                          >
                            Remover
                          </button>
                        )}
                      </div>
                    </div>

                    {(scansByTarget[target.id] ?? []).length > 0 ? (
                      <div className="border border-white/10">
                        {(scansByTarget[target.id] ?? []).slice(0, 5).map((scan) => (
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
                            <div className="flex items-center gap-3 text-xs uppercase md:justify-end">
                              <span className={`font-medium ${statusColors[scan.status]}`}>
                                {statusLabels[scan.status]}
                                {isActiveStatus(scan.status) ? (
                                  <span className="ml-1 animate-pulse">•</span>
                                ) : null}
                              </span>
                              <span className="text-slate-400">{formatDate(scan.created_at)}</span>
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
                <p className="text-xs font-semibold uppercase text-cyan-200">Resultados</p>
                <h2 className="mt-1 text-lg font-semibold text-white">
                  {scanLabels[selectedScan.scan_type]} —{" "}
                  <span className={statusColors[selectedScan.status]}>
                    {statusLabels[selectedScan.status]}
                  </span>
                </h2>
              </div>
              <div className="flex items-center gap-2">
                {isActiveStatus(selectedScan.status) ? (
                  <span className="text-xs text-slate-500">Atualizando automaticamente...</span>
                ) : null}
                {selectedScan.scan_type === "content_fuzz" || selectedScan.scan_type === "nuclei_scan" ? (
                  <button
                    className="h-9 border border-cyan-300/40 px-3 text-xs font-semibold uppercase text-cyan-100 transition hover:border-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={downloadingArtifact || selectedScan.status !== "completed"}
                    onClick={() => handleDownloadArtifact(selectedScan)}
                    type="button"
                  >
                    {downloadingArtifact
                      ? "Baixando..."
                      : selectedScan.scan_type === "nuclei_scan"
                        ? "Baixar TXT"
                        : "Baixar TXT"}
                  </button>
                ) : null}
                <button
                  className="h-9 border border-white/15 px-3 text-xs font-semibold uppercase text-slate-200 transition hover:border-cyan-300 hover:text-cyan-200"
                  onClick={() => handleLoadResults(selectedScan)}
                  type="button"
                >
                  Atualizar
                </button>
              </div>
            </div>

            {loadingResults ? (
              <div className="px-5 py-8 text-sm text-slate-400">Carregando resultados...</div>
            ) : visibleScanResults.length === 0 ? (
              <div className="px-5 py-8 text-sm text-slate-400">
                {isActiveStatus(selectedScan.status)
                  ? "Scan em andamento, nenhum resultado ainda."
                  : "Nenhum resultado encontrado para este scan."}
              </div>
            ) : (
              <div className="divide-y divide-white/10">
                {visibleScanResults.map((result) => (
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
