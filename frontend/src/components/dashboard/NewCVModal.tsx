import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiCreateCV } from "../../lib/api";
import { TEMPLATES, getTemplate, type TemplateId } from "../../lib/cv-templates";
import { CVRenderer } from "../CVRenderer";

interface NewCVModalProps {
  open: boolean;
  onClose: () => void;
  onCreated?: () => void;
}

export function NewCVModal({ open, onClose, onCreated }: NewCVModalProps) {
  const navigate = useNavigate();
  const titleRef = useRef<HTMLInputElement>(null);
  const [template, setTemplate] = useState<TemplateId>("blank");
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setTemplate("blank");
      setTitle("");
      setError("");
      setSubmitting(false);
      setTimeout(() => titleRef.current?.focus(), 50);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Poné un título para tu CV");
      titleRef.current?.focus();
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const cv = await apiCreateCV(title.trim());
      onCreated?.();
      onClose();
      navigate(`/cv/${cv.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error creando el CV");
      setSubmitting(false);
    }
  };

  const selected = getTemplate(template);
  const fakeCvForPreview = {
    id: "preview",
    title: title.trim() || "Tu CV",
    context_json: JSON.stringify(selected.context),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-cv-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="modal__head">
          <h2 id="new-cv-title" className="modal__title">
            Nuevo CV
          </h2>
          <button
            type="button"
            className="btn btn-ghost btn-compact"
            onClick={onClose}
            aria-label="Cerrar"
            style={{ fontSize: 18 }}
          >
            ✕
          </button>
        </header>

        <div className="modal__body">
          <section>
            <p className="eyebrow">1 · Plantilla</p>
            <div className="template-grid">
              {(Object.keys(TEMPLATES) as TemplateId[]).map((id) => {
                const t = TEMPLATES[id];
                const active = template === id;
                return (
                  <button
                    key={id}
                    type="button"
                    className={`template-card ${active ? "template-card--active" : ""}`}
                    onClick={() => setTemplate(id)}
                  >
                    <strong className="template-card__name">{t.name}</strong>
                    <p className="template-card__desc">{t.description}</p>
                  </button>
                );
              })}
            </div>
          </section>

          <section style={{ marginTop: 20 }}>
            <p className="eyebrow">2 · Vista previa</p>
            <div className="template-preview">
              <CVRenderer cv={fakeCvForPreview} mini />
            </div>
          </section>

          <form className="form-stack" onSubmit={handleSubmit} style={{ marginTop: 20 }}>
            <label htmlFor="cv-new-title" className="eyebrow">
              3 · Título
            </label>
            <input
              id="cv-new-title"
              ref={titleRef}
              type="text"
              className="text-input"
              placeholder='ej. "Desarrollador Fullstack"'
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              disabled={submitting}
            />

            {error && (
              <div className="flash flash-error" style={{ marginTop: 8 }}>
                {error}
              </div>
            )}

            <div className="form-actions">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={onClose}
                disabled={submitting}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={submitting || !title.trim()}
              >
                {submitting ? "Creando…" : "Crear CV"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
