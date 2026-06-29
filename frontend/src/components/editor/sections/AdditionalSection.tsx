import {
  emptyCertification,
  emptyFortaleza,
  type Certification,
  type Fortaleza,
} from "../../../types/cv";
import { TextField, TextAreaField } from "./_form";

interface AdditionalSectionProps {
  certificaciones: Certification[];
  fortalezas: Fortaleza[];
  onChangeCertificaciones: (next: Certification[]) => void;
  onChangeFortalezas: (next: Fortaleza[]) => void;
}

export function AdditionalSection({
  certificaciones,
  fortalezas,
  onChangeCertificaciones,
  onChangeFortalezas,
}: AdditionalSectionProps) {
  const updateCert = (i: number, patch: Partial<Certification>) => {
    onChangeCertificaciones(
      certificaciones.map((c, idx) => (idx === i ? { ...c, ...patch } : c))
    );
  };
  const removeCert = (i: number) =>
    onChangeCertificaciones(certificaciones.filter((_, idx) => idx !== i));
  const addCert = () => onChangeCertificaciones([...certificaciones, emptyCertification()]);

  const updateFort = (i: number, patch: Partial<Fortaleza>) => {
    onChangeFortalezas(fortalezas.map((f, idx) => (idx === i ? { ...f, ...patch } : f)));
  };
  const removeFort = (i: number) =>
    onChangeFortalezas(fortalezas.filter((_, idx) => idx !== i));
  const addFort = () => onChangeFortalezas([...fortalezas, emptyFortaleza()]);

  return (
    <section className="editor-section">
      <h3 className="editor-section__title">Adicional</h3>

      {/* Certificaciones */}
      <div className="editor-subsection">
        <div className="editor-section__head">
          <h4 className="editor-section__subtitle">Certificaciones</h4>
          <button
            type="button"
            className="btn btn-secondary btn-compact"
            onClick={addCert}
          >
            + Agregar
          </button>
        </div>
        {certificaciones.length === 0 ? (
          <p className="help">Sin certificaciones.</p>
        ) : (
          <ul className="entry-list">
            {certificaciones.map((c, i) => (
              <li key={i} className="entry-card">
                <div className="entry-card__head">
                  <strong className="entry-card__title">{c.nombre || "(sin nombre)"}</strong>
                  <button
                    type="button"
                    className="btn btn-danger btn-compact"
                    onClick={() => removeCert(i)}
                    aria-label={`Eliminar certificación ${i + 1}`}
                  >
                    Eliminar
                  </button>
                </div>
                <div className="form-row" style={{ marginTop: 12 }}>
                  <TextField
                    label="Nombre"
                    htmlFor={`cert-${i}-nombre`}
                    value={c.nombre}
                    onChange={(v) => updateCert(i, { nombre: v })}
                  />
                  <TextField
                    label="Institución"
                    htmlFor={`cert-${i}-institucion`}
                    value={c.institucion}
                    onChange={(v) => updateCert(i, { institucion: v })}
                  />
                  <TextField
                    label="Año"
                    htmlFor={`cert-${i}-fecha`}
                    value={c.fecha}
                    onChange={(v) => updateCert(i, { fecha: v })}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Fortalezas */}
      <div className="editor-subsection">
        <div className="editor-section__head">
          <h4 className="editor-section__subtitle">Fortalezas / Adicional</h4>
          <button
            type="button"
            className="btn btn-secondary btn-compact"
            onClick={addFort}
          >
            + Agregar
          </button>
        </div>
        {fortalezas.length === 0 ? (
          <p className="help">Sin fortalezas.</p>
        ) : (
          <ul className="entry-list">
            {fortalezas.map((f, i) => (
              <li key={i} className="entry-card">
                <div className="entry-card__head">
                  <strong className="entry-card__title">{f.nombre || "(sin nombre)"}</strong>
                  <button
                    type="button"
                    className="btn btn-danger btn-compact"
                    onClick={() => removeFort(i)}
                    aria-label={`Eliminar fortaleza ${i + 1}`}
                  >
                    Eliminar
                  </button>
                </div>
                <div className="form-stack" style={{ marginTop: 12 }}>
                  <TextField
                    label="Nombre"
                    htmlFor={`fort-${i}-nombre`}
                    value={f.nombre}
                    onChange={(v) => updateFort(i, { nombre: v })}
                    placeholder="Liderazgo técnico"
                  />
                  <TextAreaField
                    label="Descripción"
                    htmlFor={`fort-${i}-desc`}
                    value={f.descripcion}
                    onChange={(v) => updateFort(i, { descripcion: v })}
                    rows={2}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
