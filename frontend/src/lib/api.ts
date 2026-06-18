import { supabase, type CV, type ChatMessage } from "./supabase";

const BASE = import.meta.env.VITE_API_URL || "";

async function getToken(): Promise<string | null> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

async function authHeaders(): Promise<Record<string, string>> {
  const token = await getToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// ── CVs ──────────────────────────────────────────────

export async function apiListCVs(): Promise<CV[]> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs`, { headers });
  if (!res.ok) throw new Error(await res.text());
  const { data } = await res.json();
  return data as CV[];
}

export async function apiGetCV(id: string): Promise<CV> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs/${id}`, { headers });
  if (!res.ok) throw new Error(await res.text());
  const { data } = await res.json();
  return data as CV;
}

export async function apiCreateCV(title: string): Promise<CV> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs`, {
    method: "POST",
    headers,
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error(await res.text());
  const { data } = await res.json();
  return data as CV;
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
  const { data } = await res.json();
  return data as CV;
}

export async function apiDeleteCV(id: string): Promise<void> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs/${id}`, { method: "DELETE", headers });
  if (!res.ok) throw new Error(await res.text());
}

// ── Chat ─────────────────────────────────────────────

export async function apiGetChat(cvId: string): Promise<ChatMessage[]> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs/${cvId}/chat`, { headers });
  if (!res.ok) throw new Error(await res.text());
  const { data } = await res.json();
  return data as ChatMessage[];
}

export async function apiAppendChat(
  cvId: string,
  message: string,
  role: "user" | "assistant" = "user"
): Promise<ChatMessage> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs/${cvId}/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({ role, content: message }),
  });
  if (!res.ok) throw new Error(await res.text());
  const { data } = await res.json();
  return data as ChatMessage;
}

export async function apiClearChat(cvId: string): Promise<void> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/api/cvs/${cvId}/chat`, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) throw new Error(await res.text());
}
