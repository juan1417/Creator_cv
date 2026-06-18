import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { apiGetCV, apiUpdateCV, type CV } from "../lib/api";

export function EditorPage() {
  const { id } = useParams<{ id: string }>();
  const [cv, setCV] = useState<CV | null>(null);
  const [contextJson, setContextJson] = useState("");
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const data = await apiGetCV(id);
      setCV(data);
      setTitle(data.title);
      setContextJson(data.context_json);
    } catch (e: unknown) {
      setMessage(`Error: ${String(e)}`);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setSaving(true);
    setMessage("");
    try {
      // validate JSON
      JSON.parse(contextJson);
      const updated = await apiUpdateCV(id, {
        title: title.trim(),
        context_json: contextJson,
      });
      setCV(updated);
      setMessage("Guardado ✓");
    } catch (e: unknown) {
      if (e instanceof SyntaxError) {
        setMessage("JSON inválido — revisa la sintaxis");
      } else {
        setMessage(`Error: ${String(e)}`);
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="wrap main-content">
        <p className="empty-state">Cargando CV…</p>
      </div>
    );
  }

  if (!cv) {
    return (
      <div className="wrap main-content">
        <p className="empty-state">CV no encontrado.</p>
        <Link to="/" className="btn">
          Volver al inicio
        </Link>
      </div>
    );
  }

  return (
    <div className="wrap main-content">
      <div className="page-header">
        <Link to="/" className="page-header__back">
          <svg
            className="page-header__back-icon"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            aria-hidden="true"
          >
            <path d="M10 3L5 8l5 5" />
          </svg>
          Volver
        </Link>
        <nav className="breadcrumb" aria-label="Breadcrumb">
          <Link to="/">Mis CVs</Link>
          <span aria-hidden="true">→</span>
          <span aria-current="page">{cv.title}</span>
        </nav>
      </div>

      {message && (
        <div
          className={`flash ${message.startsWith("Error") || message.includes("inválido") ? "flash-error" : "flash-success"}`}
        >
          {message}
        </div>
      )}

      <form onSubmit={handleSave}>
        <div className="card">
          <label htmlFor="cv-title" className="eyebrow">
            Título
          </label>
          <input
            id="cv-title"
            type="text"
            className="text-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            style={{ marginTop: 8 }}
          />
        </div>

        <div className="card">
          <label htmlFor="cv-json" className="eyebrow">
            Contexto JSON
          </label>
          <p className="help">
            Edita el JSON directamente. El preview se renderiza desde este
            contenido.
          </p>
          <textarea
            id="cv-json"
            className="code-area"
            value={contextJson}
            onChange={(e) => setContextJson(e.target.value)}
            spellCheck={false}
          />
        </div>

        <div className="form-actions" style={{ marginBottom: 32 }}>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={saving}
          >
            {saving ? "Guardando…" : "Guardar cambios"}
          </button>
          <Link
            to={`/cv/${id}/preview`}
            className="btn btn-secondary"
          >
            Vista previa
          </Link>
        </div>
      </form>
    </div>
  );
}
