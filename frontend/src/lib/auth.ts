export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export type UserRole = "admin" | "pentester" | "viewer";

export type CurrentUser = {
  id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
};

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

export async function fetchCurrentUser(): Promise<CurrentUser | null> {
  try {
    const response = await fetch(`${API_URL}/auth/me`, {
      credentials: "include",
    });
    if (!response.ok) return null;
    return (await response.json()) as CurrentUser;
  } catch {
    return null;
  }
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response | null> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
  });

  if (response.status === 401 || response.status === 403) {
    window.location.href = "/";
    return null;
  }

  return response;
}
