import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  apiDeleteCV,
  apiDuplicateCV,
  type CV,
} from "../../lib/api";
import { completionPercent, parseContext } from "../../types/cv";
import { CVRenderer } from "../CVRenderer";

interface CVCardProps {
  cv: CV;
  onChanged: () => void;
}

export function CVCard({ cv, onChanged }: CVCardProps) {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const ctx = parseContext(cv.context_json);
  const completion = completionPercent(ctx);
  const updated = new Date(cv.updated_at).toLocaleDateString("es-ES", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  const handleDelete = async () => {
    if (!confirm(`¿Eliminar "${cv.title}"? Esta acción no se puede deshacer.`)) return;
    setBusy(true);
    setError("");
    try {
      await apiDeleteCV(cv.id);
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al eliminar");
    } finally {
      setBusy(false);
    }
  };

  const handleDuplicate = async () => {
    setBusy(true);
    setError("");
    try {
      const copy = await apiDuplicateCV(cv.id);
      onChanged();
      navigate(`/cv/${copy.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al duplicar");
      setBusy(false);
    }
  };

  return (
    <article className="cv-card">
      <Link to={`/cv/${cv.id}`} className="cv-card__thumb-link" aria-label={`Abrir ${cv.title}`}>
        <CVRenderer cv={cv} mini />
      </Link>

      <div className="cv-card__body">
        <div className="cv-card__head">
          <Link to={`/cv/${cv.id}`} className="cv-card__title">
            {cv.title}
          </Link>
          <span
            className={`cv-card__badge cv-card__badge--${completionBadgeTier(completion)}`}
            title={`${completion}% completo`}
          >
            {completion}%
          </span>
        </div>

        <p className="cv-card__meta">
          Actualizado {updated}
        </p>

        {error && <p className="cv-card__error">{error}</p>}

        <div className="cv-card__actions">
          <Link to={`/cv/${cv.id}`} className="btn btn-primary btn-compact">
            Abrir
          </Link>
          <Link
            to={`/cv/${cv.id}/preview`}
            className="btn btn-secondary btn-compact"
          >
            Vista previa
          </Link>
          <button
            type="button"
            className="btn btn-ghost btn-compact"
            onClick={handleDuplicate}
            disabled={busy}
          >
            Duplicar
          </button>
          <button
            type="button"
            className="btn btn-danger btn-compact"
            onClick={handleDelete}
            disabled={busy}
          >
            Eliminar
          </button>
        </div>
      </div>
    </article>
  );
}

function completionBadgeTier(pct: number): "ok" | "mid" | "low" {
  if (pct >= 75) return "ok";
  if (pct >= 40) return "mid";
  return "low";
}
