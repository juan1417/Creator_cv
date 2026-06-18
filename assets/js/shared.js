// Utilidades compartidas entre páginas.

function flash(message, kind = "info") {
  const root = document.getElementById("flash-root");
  if (!root) {
    alert(message);
    return;
  }
  const el = document.createElement("p");
  el.className = `flash flash-${kind}`;
  el.setAttribute("role", kind === "error" ? "alert" : "status");
  el.textContent = message;
  root.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function downloadText(text, filename, mime = "text/plain;charset=utf-8") {
  downloadBlob(new Blob([text], { type: mime }), filename);
}

function getQueryParam(name) {
  const u = new URL(window.location.href);
  return u.searchParams.get(name);
}

function sanitizeFilename(s) {
  return (s || "cv")
    .replace(/[^\w\sÀ-ſ.-]+/g, "")
    .replace(/\s+/g, "-")
    .toLowerCase()
    .slice(0, 60) || "cv";
}

window.Shared = { flash, escapeHtml, formatDate, downloadBlob, downloadText, getQueryParam, sanitizeFilename };
