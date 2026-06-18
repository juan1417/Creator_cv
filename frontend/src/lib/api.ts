const BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

function getToken(): string | null {
  return localStorage.getItem("token");
}

async function authHeaders(): Promise<Record<string, string>> {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// ── Auth ──────────────────────────────────────────────

export async function apiRegister(
  email: string,
  password: string
): Promise<{ token: string; user_id: string; email: string }> {
  const res = await fetch(`${BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "Error al registrarse");
  return body;
}

export async function apiLogin(
  email: string,
  password: string
): Promise<{ token: string; user_id: string; email: string }> {
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "Error al iniciar sesión");
  return body;
}

export async function apiMe(): Promise<{ user_id: string; email: string }> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/auth/me`, { headers });
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "No autenticado");
  return body;
}

// ── CVs ──────────────────────────────────────────────

export type CV = {
  id: string;
  title: string;
  context_json: string;
  created_at: string;
  updated_at: string;
};

export async function apiListCVs(): Promise<CV[]> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs`, { headers });
  if (!res.ok) throw new Error(await res.text());
  const { cvs } = await res.json();
  return cvs as CV[];
}

export async function apiGetCV(id: string): Promise<CV> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs/${id}`, { headers });
  if (!res.ok) throw new Error(await res.text());
  const { cv } = await res.json();
  return cv as CV;
}

export async function apiCreateCV(title: string): Promise<CV> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs`, {
    method: "POST",
    headers,
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error(await res.text());
  const { cv } = await res.json();
  return cv as CV;
}

export async function apiUpdateCV(
  id: string,
  body: { title?: string; context_json?: string }
): Promise<CV> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs/${id}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  const { cv } = await res.json();
  return cv as CV;
}

export async function apiDeleteCV(id: string): Promise<void> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs/${id}`, { method: "DELETE", headers });
  if (!res.ok) throw new Error(await res.text());
}

// ── Chat ─────────────────────────────────────────────

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  patch?: Record<string, unknown> | null;
  created_at: string;
};

export async function apiGetChat(cvId: string): Promise<ChatMessage[]> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs/${cvId}/chat`, { headers });
  if (!res.ok) throw new Error(await res.text());
  const { messages } = await res.json();
  return messages as ChatMessage[];
}

export async function apiAppendChat(
  cvId: string,
  content: string,
  role: "user" | "assistant" = "user"
): Promise<ChatMessage> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs/${cvId}/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({ role, content }),
  });
  if (!res.ok) throw new Error(await res.text());
  const { message } = await res.json();
  return message as ChatMessage;
}

export async function apiClearChat(cvId: string): Promise<void> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs/${cvId}/chat`, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) throw new Error(await res.text());
}
