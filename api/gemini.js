// Vercel Serverless Function: proxy a Google Gemini.
// Mantiene GEMINI_API_KEY fuera del navegador.
// Input:  POST { cv_id, user_capacity, messages: [{role, content}], cv_context }
// Output: { ok: true, assistant: "...", patch: {...} | null }

const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models";
const PRIMARY_MODEL = process.env.GEMINI_MODEL || "gemini-2.5-flash";
const FALLBACK_MODELS = (process.env.GEMINI_MODEL_FALLBACKS || "gemini-2.0-flash,gemini-1.5-flash")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

const SYSTEM_PROMPT = `Sos un asistente que ayuda a una persona a completar/afinar su CV.
Tu objetivo: hacer preguntas cortas y concretas para obtener datos del usuario
(según su nivel: principiante = pocas preguntas y simples, intermedio = equilibrado,
avanzado = más detalle e impacto con métricas).

REGLAS:
- NO inventes datos. Si el usuario no dice algo, preguntalo.
- Sé breve (2-4 oraciones por respuesta).
- Cuando el usuario confirme datos que faltan, podés proponer un "patch" JSON.
- El patch debe tener exactamente las claves del esquema del CV del usuario
  (meta, perfil_profesional, experiencia, educacion, habilidades, proyectos,
  recursos_actuales, restricciones, dudas_pendientes, certificaciones, fortalezas).
- NO inventes fechas, empresas, ni logros. Solo lo que el usuario te confirmó.

FORMATO DE SALIDA (JSON estricto, sin texto extra):
{
  "assistant": "tu respuesta al usuario (texto plano)",
  "patch": null | { ...sub-set del JSON del CV... }
}`;

async function callGemini(apiKey, model, payload) {
  const url = `${GEMINI_API_URL}/${model}:generateContent?key=${apiKey}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    const err = new Error(data.error?.message || `Gemini ${res.status}`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

function extractTextAndPatch(data) {
  const cand = data.candidates?.[0];
  const text = cand?.content?.parts?.map((p) => p.text || "").join("") || "";
  // Buscar primer bloque JSON en el texto
  const match = text.match(/\{[\s\S]*\}/);
  if (!match) {
    return { assistant: text.trim() || "(sin respuesta)", patch: null };
  }
  try {
    const parsed = JSON.parse(match[0]);
    return {
      assistant: String(parsed.assistant || text.trim()),
      patch: parsed.patch || null,
    };
  } catch {
    return { assistant: text.trim(), patch: null };
  }
}

function buildPayload(messages, capacity, cvContext) {
  const contents = [
    {
      role: "user",
      parts: [{ text: SYSTEM_PROMPT + `\n\nNivel del usuario: ${capacity}.\n\nContexto actual del CV (puede estar incompleto):\n${JSON.stringify(cvContext, null, 2)}` }],
    },
    {
      role: "model",
      parts: [{ text: "Entendido. Empiezo con la primera pregunta." }],
    },
  ];
  for (const m of messages || []) {
    contents.push({
      role: m.role === "user" ? "user" : "model",
      parts: [{ text: String(m.content || "") }],
    });
  }
  return {
    contents,
    generationConfig: { temperature: 0.7, maxOutputTokens: 1024 },
  };
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.status(405).json({ ok: false, error: "Method not allowed" });
    return;
  }
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    res.status(500).json({ ok: false, error: "Falta GEMINI_API_KEY en el servidor." });
    return;
  }
  try {
    const body = req.body || {};
    const { messages = [], user_capacity = "intermedio", cv_context = {} } = body;
    const payload = buildPayload(messages, user_capacity, cv_context);

    const models = [PRIMARY_MODEL, ...FALLBACK_MODELS];
    let lastErr = null;
    for (const model of models) {
      try {
        const data = await callGemini(apiKey, model, payload);
        const { assistant, patch } = extractTextAndPatch(data);
        res.status(200).json({ ok: true, assistant, patch, model });
        return;
      } catch (e) {
        lastErr = e;
        if (e.status === 429 || e.status >= 500) {
          continue; // try next fallback
        }
        throw e; // 4xx no transitorio
      }
    }
    throw lastErr || new Error("Todos los modelos fallaron");
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message || "Error interno" });
  }
}
