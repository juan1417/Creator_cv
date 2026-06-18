import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { apiGetCV } from "../lib/api";
import { CVRenderer } from "../components/CVRenderer";
import type { CV } from "../lib/supabase";

export function PreviewPage() {
  const { id } = useParams<{ id: string }>();
  const [cv, setCV] = useState<CV | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const data = await apiGetCV(id);
      setCV(data);
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="wrap main-content">
      <div className="page-header">
        <Link to={`/cv/${id}`} className="page-header__back">
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
          Editor
        </Link>
        <nav className="breadcrumb" aria-label="Breadcrumb">
          <Link to="/">Mis CVs</Link>
          <span aria-hidden="true">→</span>
          <Link to={`/cv/${id}`}>{cv?.title ?? "…"}</Link>
          <span aria-hidden="true">→</span>
          <span aria-current="page">Vista previa</span>
        </nav>
      </div>

      {loading && <p className="empty-state">Cargando…</p>}
      {error && (
        <div className="flash flash-error">{error}</div>
      )}

      {cv && (
        <div className="preview-doc-stage">
          <CVRenderer cv={cv} />
        </div>
      )}
    </div>
  );
}
