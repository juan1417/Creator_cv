import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiListCVs, apiCreateCV, apiDeleteCV } from "../lib/api";
import type { CV } from "../lib/supabase";

export function HomePage() {
  const [cvs, setCVs] = useState<CV[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const load = async () => {
    try {
      setError("");
      const list = await apiListCVs();
      setCVs(list);
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const cv = await apiCreateCV(title.trim());
      navigate(`/cv/${cv.id}`);
    } catch (e: unknown) {
      setError(String(e));
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("¿Eliminar este CV?")) return;
    try {
      await apiDeleteCV(id);
      setCVs((prev) => prev.filter((cv) => cv.id !== id));
    } catch (e: unknown) {
      setError(String(e));
    }
  };

  return (
    <div className="wrap main-content">
      <h1>Mis CVs</h1>
      <p className="lede">Gestiona tus currículums vitae.</p>

      {error && (
        <div className="flash flash-error" style={{ marginTop: 16 }}>
          {error}
        </div>
      )}

      <section className="page-section card">
        <h2 className="eyebrow">Nuevo</h2>
        <form className="form-inline" onSubmit={handleCreate}>
          <input
            type="text"
            className="text-input"
            placeholder="Título del CV (ej. Desarrollador Fullstack)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            style={{ minWidth: 280, flex: 1 }}
          />
          <button type="submit" className="btn btn-primary">
            Crear CV
          </button>
        </form>
      </section>

      <section className="page-section">
        <h2 className="eyebrow">Tus CVs</h2>

        {loading ? (
          <p className="empty-state">Cargando…</p>
        ) : cvs.length === 0 ? (
          <p className="empty-state">Aún no tienes ningún CV. ¡Crea uno arriba!</p>
        ) : (
          <ul className="cv-list" style={{ marginTop: 16 }}>
            {cvs.map((cv) => (
              <li key={cv.id}>
                <Link to={`/cv/${cv.id}`}>{cv.title}</Link>
                <span className="meta-muted">
                  {new Date(cv.updated_at).toLocaleDateString("es-ES")}
                </span>
                <Link
                  to={`/cv/${cv.id}/preview`}
                  className="btn btn-secondary btn-compact"
                >
                  Vista previa
                </Link>
                <button
                  className="btn btn-danger btn-compact"
                  onClick={() => handleDelete(cv.id)}
                >
                  Eliminar
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
