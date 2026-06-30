import { emptyCertification, emptyFortaleza, type Certification, type Fortaleza } from "../../../types/cv";

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
  return (
    <>
      {/* Certificaciones */}
      <CertificacionesSection value={certificaciones} onChange={onChangeCertificaciones} />
      {/* Fortalezas */}
      <FortalezasSection value={fortalezas} onChange={onChangeFortalezas} />
    </>
  );
}

function CertificacionesSection({ value, onChange }: { value: Certification[]; onChange: (n: Certification[]) => void }) {
  const update = (i: number, patch: Partial<Certification>) =>
    onChange(value.map((c, idx) => (idx === i ? { ...c, ...patch } : c)));
  const remove = (i: number) => onChange(value.filter((_, idx) => idx !== i));
  const add = () => onChange([...value, emptyCertification()]);

  return (
    <div className="section-group">
      <div className="section-group-header">
        <div className="section-group-title">Certificaciones</div>
        <button className="btn btn-s btn-sm" type="button" onClick={add}>+ Agregar</button>
      </div>
      <div className="section-card">
        {value.length === 0 ? (
          <p style={{ color: "var(--muted)", fontSize: 13 }}>Sin certificaciones.</p>
        ) : (
          value.map((c, i) => (
            <div key={i} className="cv-item">
              <div className="cv-item-header">
                <div>
                  <div className="cv-item-title">{c.nombre || "(sin nombre)"}</div>
                  <div className="cv-item-subtitle">{[c.institucion, c.fecha].filter(Boolean).join(" · ")}</div>
                </div>
                <div className="cv-item-actions">
                  <button className="cv-item-btn" title="Eliminar" type="button" onClick={() => remove(i)}>✕</button>
                </div>
              </div>
              <div className="form-row" style={{ marginTop: 12 }} onClick={(e) => e.stopPropagation()}>
                <div className="form-group">
                  <label className="form-label">Nombre</label>
                  <input className="form-input" type="text" value={c.nombre} onChange={(e) => update(i, { nombre: e.target.value })} placeholder="AWS Solutions Architect" />
                </div>
                <div className="form-group">
                  <label className="form-label">Institución</label>
                  <input className="form-input" type="text" value={c.institucion} onChange={(e) => update(i, { institucion: e.target.value })} placeholder="Amazon Web Services" />
                </div>
                <div className="form-group">
                  <label className="form-label">Año</label>
                  <input className="form-input" type="text" value={c.fecha} onChange={(e) => update(i, { fecha: e.target.value })} placeholder="2024" />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function FortalezasSection({ value, onChange }: { value: Fortaleza[]; onChange: (n: Fortaleza[]) => void }) {
  const update = (i: number, patch: Partial<Fortaleza>) =>
    onChange(value.map((f, idx) => (idx === i ? { ...f, ...patch } : f)));
  const remove = (i: number) => onChange(value.filter((_, idx) => idx !== i));
  const add = () => onChange([...value, emptyFortaleza()]);

  return (
    <div className="section-group">
      <div className="section-group-header">
        <div className="section-group-title">Fortalezas / Adicional</div>
        <button className="btn btn-s btn-sm" type="button" onClick={add}>+ Agregar</button>
      </div>
      <div className="section-card">
        {value.length === 0 ? (
          <p style={{ color: "var(--muted)", fontSize: 13 }}>Sin fortalezas.</p>
        ) : (
          value.map((f, i) => (
            <div key={i} className="cv-item">
              <div className="cv-item-header">
                <div>
                  <div className="cv-item-title">{f.nombre || "(sin nombre)"}</div>
                </div>
                <div className="cv-item-actions">
                  <button className="cv-item-btn" title="Eliminar" type="button" onClick={() => remove(i)}>✕</button>
                </div>
              </div>
              <div className="form-row" style={{ marginTop: 12 }} onClick={(e) => e.stopPropagation()}>
                <div className="form-group">
                  <label className="form-label">Nombre</label>
                  <input className="form-input" type="text" value={f.nombre} onChange={(e) => update(i, { nombre: e.target.value })} placeholder="Liderazgo técnico" />
                </div>
                <div className="form-group">
                  <label className="form-label">Descripción</label>
                  <textarea className="form-input form-textarea" rows={2} value={f.descripcion} onChange={(e) => update(i, { descripcion: e.target.value })} />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
