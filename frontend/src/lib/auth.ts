export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export type UserRole = "admin" | "pentester" | "viewer";

export type CurrentUser = {
  id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
};

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return (
    window.localStorage.getItem("access_token") ??
    window.sessionStorage.getItem("access_token")
  );
}

export function clearStoredToken(): void {
  window.localStorage.removeItem("access_token");
  window.sessionStorage.removeItem("access_token");
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

export async function fetchCurrentUser(): Promise<CurrentUser | null> {
  const token = getStoredToken();
  if (!token) return null;
  try {
    const response = await fetch(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) return null;
    return (await response.json()) as CurrentUser;
  } catch {
    return null;
  }
}
