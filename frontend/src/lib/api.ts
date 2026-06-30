const BASE = import.meta.env.VITE_API_URL || "";

// ── Token storage ────────────────────────────────────────────────────────
//
// Access token (15 min) + refresh token (30 d) se guardan separados en
// localStorage. El helper ``authedFetch`` reintenta una vez con un refresh
// si recibe 401.

export function getAccessToken(): string | null {
  return localStorage.getItem("access_token");
}

export function getRefreshToken(): string | null {
  return localStorage.getItem("refresh_token");
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

export function clearTokens(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

// ── Refresh ──────────────────────────────────────────────────────────────
//
// Si varias requests 401 a la vez, sólo se hace UN refresh (los demás esperan).

let refreshInFlight: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight;

  const refresh = getRefreshToken();
  if (!refresh) return false;

  refreshInFlight = (async () => {
    try {
      const res = await fetch(`${BASE}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) return false;
      const data = (await res.json()) as { access_token: string; refresh_token: string };
      setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

// ── authedFetch ──────────────────────────────────────────────────────────
//
// Wrapper sobre ``fetch`` que:
// 1. Agrega Authorization con el access token.
// 2. Si la respuesta es 401, intenta refresh + retry una vez.
// 3. Si el refresh falla, limpia tokens y propaga el 401.

export async function authedFetch(
  url: string,
  options: RequestInit = {},
  onSessionExpired?: () => void
): Promise<Response> {
  const doFetch = (token: string | null) =>
    fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

  let res = await doFetch(getAccessToken());
  if (res.status !== 401) return res;

  const refreshed = await tryRefresh();
  if (!refreshed) {
    clearTokens();
    onSessionExpired?.();
    return res;
  }
  res = await doFetch(getAccessToken());
  return res;
}

// ── Auth ────────────────────────────────────────────────────────────────

export type LoginResult = {
  access_token: string;
  refresh_token: string;
  user_id: string;
  email: string;
};

export type LoginPendingResult = {
  requires_2fa: true;
  pending_token: string;
  user_id: string;
  email: string;
};

export type LoginOrPending = LoginResult | LoginPendingResult;

export function isPending(result: LoginOrPending): result is LoginPendingResult {
  return (result as LoginPendingResult).requires_2fa === true;
}

// Re-export para uso en LoginPage (debe vivir en api porque necesita el type guard).

export type RegisterResult = {
  user_id: string;
  email: string;
  requires_verification: boolean;
  /** Solo presente cuando ``requires_verification=false`` (modo dev). */
  access_token?: string;
  refresh_token?: string;
};

export async function apiRegister(
  email: string,
  password: string
): Promise<RegisterResult> {
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
  password: string,
  onSessionExpired?: () => void
): Promise<LoginOrPending> {
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "Error al iniciar sesión");
  if (isPending(body)) return body;
  setTokens(body.access_token, body.refresh_token);
  return body;
}

export async function apiVerifyEmail(token: string): Promise<LoginOrPending> {
  const res = await fetch(`${BASE}/api/auth/verify-email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "Enlace inválido o expirado");
  if (!isPending(body)) setTokens(body.access_token, body.refresh_token);
  return body;
}

export async function apiVerifyTwoFactor(
  pendingToken: string,
  code: string
): Promise<LoginResult> {
  const res = await fetch(`${BASE}/api/auth/2fa/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pending_token: pendingToken, code }),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "Código inválido");
  setTokens(body.access_token, body.refresh_token);
  return body;
}

export async function apiMe(onSessionExpired?: () => void): Promise<{ user_id: string; email: string }> {
  const res = await authedFetch(
    `${BASE}/api/auth/me`,
    {},
    onSessionExpired
  );
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "No autenticado");
  return body;
}

export async function apiLogout(onSessionExpired?: () => void): Promise<void> {
  // Best-effort: intentar revocar el refresh server-side.
  const refresh = getRefreshToken();
  try {
    if (refresh) {
      await authedFetch(
        `${BASE}/api/auth/logout`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refresh }),
        },
        onSessionExpired
      );
    }
  } catch {
    // ignorar — logout local igual limpia
  }
  clearTokens();
}

export async function apiResendVerification(email: string): Promise<void> {
  const res = await fetch(`${BASE}/api/auth/resend-verification`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || "No se pudo reenviar el email");
  }
}

export async function apiForgotPassword(email: string): Promise<void> {
  const res = await fetch(`${BASE}/api/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || "No se pudo procesar la solicitud");
  }
}

export async function apiResetPassword(token: string, newPassword: string): Promise<void> {
  const res = await fetch(`${BASE}/api/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || "No se pudo restablecer la contraseña");
  }
}

// ── 2FA management ──────────────────────────────────────────────────────

export type TotpSetupStart = {
  qr_data_url: string;
  manual_key: string;
  otpauth_uri: string;
};

export async function apiTotpSetupStart(
  onSessionExpired?: () => void
): Promise<TotpSetupStart> {
  const res = await authedFetch(
    `${BASE}/api/auth/2fa/setup`,
    { method: "POST" },
    onSessionExpired
  );
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "No se pudo iniciar el setup");
  return body;
}

export async function apiTotpSetupConfirm(
  code: string,
  onSessionExpired?: () => void
): Promise<{ backup_codes: string[] }> {
  const res = await authedFetch(
    `${BASE}/api/auth/2fa/verify-setup`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    },
    onSessionExpired
  );
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "Código inválido");
  return body;
}

export async function apiTotpDisable(
  password: string,
  code: string,
  onSessionExpired?: () => void
): Promise<void> {
  const res = await authedFetch(
    `${BASE}/api/auth/2fa/disable`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password, code }),
    },
    onSessionExpired
  );
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || "No se pudo desactivar 2FA");
  }
}

export async function apiBackupCodesRegenerate(
  password: string,
  onSessionExpired?: () => void
): Promise<{ backup_codes: string[] }> {
  const res = await authedFetch(
    `${BASE}/api/auth/2fa/backup-codes`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    },
    onSessionExpired
  );
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "No se pudo regenerar");
  return body;
}

// ── CVs ────────────────────────────────────────────────────────────────

export type CV = {
  id: string;
  title: string;
  context_json: string;
  created_at: string;
  updated_at: string;
};

export async function apiListCVs(onSessionExpired?: () => void): Promise<CV[]> {
  const res = await authedFetch(`${BASE}/api/cvs`, {}, onSessionExpired);
  if (!res.ok) throw new Error(await res.text());
  const { cvs } = await res.json();
  return cvs as CV[];
}

export async function apiGetCV(id: string, onSessionExpired?: () => void): Promise<CV> {
  const res = await authedFetch(`${BASE}/api/cvs/${id}`, {}, onSessionExpired);
  if (!res.ok) throw new Error(await res.text());
  const { cv } = await res.json();
  return cv as CV;
}

export async function apiCreateCV(
  title: string,
  contextJson?: string,
  onSessionExpired?: () => void
): Promise<CV> {
  const res = await authedFetch(
    `${BASE}/api/cvs`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, context_json: contextJson }),
    },
    onSessionExpired
  );
  if (!res.ok) throw new Error(await res.text());
  const { cv } = await res.json();
  return cv as CV;
}

export async function apiUpdateCV(
  id: string,
  body: { title?: string; context_json?: string },
  onSessionExpired?: () => void
): Promise<CV> {
  const res = await authedFetch(
    `${BASE}/api/cvs/${id}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    onSessionExpired
  );
  if (!res.ok) throw new Error(await res.text());
  const { cv } = await res.json();
  return cv as CV;
}

export async function apiDeleteCV(
  id: string,
  onSessionExpired?: () => void
): Promise<void> {
  const res = await authedFetch(
    `${BASE}/api/cvs/${id}`,
    { method: "DELETE" },
    onSessionExpired
  );
  if (!res.ok) throw new Error(await res.text());
}

export async function apiDuplicateCV(
  id: string,
  onSessionExpired?: () => void
): Promise<CV> {
  const res = await authedFetch(
    `${BASE}/api/cvs/${id}/duplicate`,
    { method: "POST" },
    onSessionExpired
  );
  if (!res.ok) throw new Error(await res.text());
  const { cv } = await res.json();
  return cv as CV;
}

// ── Chat ───────────────────────────────────────────────────────────────

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  patch?: Record<string, unknown> | null;
  created_at: string;
};

export async function apiGetChat(
  cvId: string,
  onSessionExpired?: () => void
): Promise<ChatMessage[]> {
  const res = await authedFetch(
    `${BASE}/api/cvs/${cvId}/chat`,
    {},
    onSessionExpired
  );
  if (!res.ok) throw new Error(await res.text());
  const { messages } = await res.json();
  return messages as ChatMessage[];
}

export async function apiAppendChat(
  cvId: string,
  content: string,
  role: "user" | "assistant" = "user",
  onSessionExpired?: () => void
): Promise<ChatMessage> {
  const res = await authedFetch(
    `${BASE}/api/cvs/${cvId}/chat`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role, content }),
    },
    onSessionExpired
  );
  if (!res.ok) throw new Error(await res.text());
  const { message } = await res.json();
  return message as ChatMessage;
}

export async function apiClearChat(
  cvId: string,
  onSessionExpired?: () => void
): Promise<void> {
  const res = await authedFetch(
    `${BASE}/api/cvs/${cvId}/chat`,
    { method: "DELETE" },
    onSessionExpired
  );
  if (!res.ok) throw new Error(await res.text());
}

// ── Compare ─────────────────────────────────────────────────────────

export type CompareResult = {
  score: number;
  verdict: string;
  sub_scores: Record<string, number>;
  improvements: Array<{ title: string; description: string; priority: string }>;
  strengths: string[];
  gaps: string[];
};

export async function apiCompareCV(
  cvId: string,
  jobTitle: string,
  jobDescription: string,
  onSessionExpired?: () => void
): Promise<CompareResult> {
  const res = await authedFetch(
    `${BASE}/api/compare`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cv_id: cvId, job_title: jobTitle, job_description: jobDescription }),
    },
    onSessionExpired
  );
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "Error al comparar");
  return body as CompareResult;
}

// ── History ──────────────────────────────────────────────────────────────

export interface HistoryEntry {
  id: string;
  cv_id: string;
  event_type: "created" | "edited" | "duplicated";
  title: string;
  description: string;
  created_at: string;
}

export async function apiGetHistory(
  cvId?: string,
  onSessionExpired?: () => void
): Promise<HistoryEntry[]> {
  const params = new URLSearchParams();
  if (cvId) params.set("cv_id", cvId);
  const url = `${BASE}/api/history${params.toString() ? `?${params}` : ""}`;
  const res = await authedFetch(url, {}, onSessionExpired);
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "Error al obtener historial");
  return body.entries ?? [];
}

export async function apiRestoreHistory(
  entryId: string,
  onSessionExpired?: () => void
): Promise<Record<string, unknown>> {
  const res = await authedFetch(
    `${BASE}/api/history/${entryId}/restore`,
    { method: "POST" },
    onSessionExpired
  );
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "Error al restaurar");
  return body.snapshot as Record<string, unknown>;
}
