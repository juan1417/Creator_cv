import { useEffect, useMemo, useRef, useState } from "react";
import type { CV } from "../lib/api";
import { parseContext, type CVContext, type CVSettings, type Experience } from "../types/cv";

interface CVRendererProps {
  cv: CV;
  settings?: CVSettings;
  /** Modo "mini" para thumbnails en el dashboard. */
  mini?: boolean;
}

// 210mm en píxeles (96 DPI): 210 × 96 / 25.4
const A4_WIDTH_PX = 793.7;

/** Renderiza el CV en hoja A4 (blanca). Fuente única de verdad para preview + thumbnails. */
export function CVRenderer({ cv, settings, mini = false }: CVRendererProps) {
  const data: CVContext = useMemo(() => parseContext(cv.context_json), [cv.context_json]);

  const style: React.CSSProperties = useMemo(() => {
    if (!settings) return {};
    const fontMap: Record<string, string> = {
      system: '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif',
      georgia: 'Georgia, "Times New Roman", serif',
      garamond: '"EB Garamond", Garamond, serif',
      helvetica: 'Helvetica, Arial, sans-serif',
    };
    return {
      "--cv-accent": settings.accentColor,
      "--cv-font": fontMap[settings.fontFamily] || fontMap.system,
      "--cv-font-size": `${settings.fontSize}px`,
      "--cv-line-height": settings.lineHeight,
    } as React.CSSProperties;
  }, [settings]);

  if (mini) {
    return <Thumbnail data={data} />;
  }

  const vs = settings?.visibleSections;

  return (
    <div className="cv-paper" style={style}>
      <div className="cv-ref">
        <CVBody data={data} visibleSections={vs} />
      </div>
    </div>
  );
}

/** Thumbnail escalado al ancho del contenedor (escala CSS transform). */
function Thumbnail({ data }: { data: CVContext }) {
  const ref = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0.3);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const update = () => {
      const w = el.clientWidth;
      if (w > 0) setScale(w / A4_WIDTH_PX);
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div ref={ref} className="cv-thumb" aria-hidden="true">
      <div
        className="cv-thumb__paper"
        style={{ transform: `scale(${scale})` }}
      >
        <div className="cv-ref">
          <CVBody data={data} />
        </div>
      </div>
    </div>
  );
}

function CVBody({ data, visibleSections }: { data: CVContext; visibleSections?: Record<string, boolean> }) {
  const m = data.meta;
  const nombre = m.nombre_completo.trim();
  const tituloProf = m.titulo_profesional.trim();
  const contactLine = buildContactLine(m);

  const resumen = m.objetivo_cv.trim();
  const show = (key: string) => !visibleSections || visibleSections[key] !== false;

  return (
    <>
      {/* Header */}
      {(nombre || tituloProf || contactLine.length > 0) && (
        <header className="cv-ref__header">
          {nombre && <h1 className="cv-ref__name">{nombre}</h1>}
          {tituloProf && (
            <p className="cv-ref__role">{tituloProf}</p>
          )}
          {contactLine.length > 0 && (
            <p className="cv-ref__contact-line">
              {contactLine.map((item, i) => (
                <span key={i}>
                  {i > 0 && <span className="cv-ref__sep">|</span>}
                  <span className="cv-ref__contact-val">{item}</span>
                </span>
              ))}
            </p>
          )}
        </header>
      )}

      {/* Perfil Profesional */}
      {show("summary") && resumen && (
        <Section title="Perfil Profesional">
          <p className="cv-ref__para">{resumen}</p>
        </Section>
      )}

      {/* Experiencia */}
      {show("experience") && data.experiencia.length > 0 && (
        <Section title="Experiencia">
          {data.experiencia.map((exp, i) => (
            <ExperienceEntry key={i} exp={exp} />
          ))}
        </Section>
      )}

      {/* Habilidades */}
      {show("skills") && hasAnySkill(data.habilidades) && (
        <Section title="Habilidades">
          <SkillRow label="Técnicas" values={data.habilidades.tecnicas} />
          <SkillRow label="Habilidades Blandas" values={data.habilidades.blandas} />
          <SkillRow label="Idiomas" values={data.habilidades.idiomas} />
          <SkillRow label="Tecnologías" values={data.habilidades.tecnologias} />
        </Section>
      )}

      {/* Educación y Certificaciones */}
      {show("education") && (data.educacion.length > 0 || data.certificaciones.length > 0) && (
        <Section title="Educación y Certificaciones">
          {data.educacion.map((edu, i) => (
            <div key={`edu-${i}`} className="cv-ref__entry">
              <div className="cv-ref__entry-head">
                <div className="cv-ref__entry-main">
                  {edu.titulo && (
                    <span className="cv-ref__entry-role">{edu.titulo}</span>
                  )}
                  {edu.institucion && (
                    <>
                      {" "}
                      <span className="cv-ref__entry-org">— {edu.institucion}</span>
                    </>
                  )}
                </div>
                <div className="cv-ref__entry-aside">
                  {edu.fecha_fin && (
                    <div className="cv-ref__entry-date">{formatDate(edu.fecha_fin)}</div>
                  )}
                </div>
              </div>
              {edu.descripcion && <p className="cv-ref__para">{edu.descripcion}</p>}
            </div>
          ))}
          {data.certificaciones.map((cert, i) => (
            <p key={`cert-${i}`} className="cv-ref__para">
              {cert.nombre}
              {cert.institucion ? ` — ${cert.institucion}` : ""}
              {cert.fecha ? ` (${cert.fecha})` : ""}
            </p>
          ))}
        </Section>
      )}

      {/* Proyectos */}
      {show("projects") && data.proyectos.length > 0 && (
        <Section title="Proyectos">
          {data.proyectos.map((proj, i) => (
            <div key={i} className="cv-ref__entry">
              <p className="cv-ref__proj-name">{proj.nombre}</p>
              <div className="cv-ref__proj-meta">
                {proj.rol && <span>Rol: {proj.rol}</span>}
                {proj.tecnologias.length > 0 && (
                  <span>Tecnologías: {proj.tecnologias.join(", ")}</span>
                )}
                {proj.url && (
                  <a
                    className="cv-ref__proj-link-anchor"
                    href={proj.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {proj.url}
                  </a>
                )}
              </div>
              {proj.descripcion && (
                <p className="cv-ref__para" style={{ marginTop: 4 }}>
                  {proj.descripcion}
                </p>
              )}
            </div>
          ))}
        </Section>
      )}

      {/* Fortalezas */}
      {data.fortalezas.length > 0 && (
        <Section title="Adicional">
          {data.fortalezas.map((f, i) => (
            <p key={i} className="cv-ref__para">
              {f.nombre || f.descripcion}
            </p>
          ))}
        </Section>
      )}
    </>
  );
}

// ── Sub-components ───────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="cv-ref__section">
      <h2 className="cv-ref__section-title">{title}</h2>
      {children}
    </div>
  );
}

function ExperienceEntry({ exp }: { exp: Experience }) {
  const fechaInicio = formatDate(exp.fecha_inicio);
  const fechaFin = formatDate(exp.fecha_fin);

  return (
    <div className="cv-ref__entry">
      <div className="cv-ref__entry-head">
        <div className="cv-ref__entry-main">
          {exp.puesto && <span className="cv-ref__entry-role">{exp.puesto}</span>}
          {exp.empresa && (
            <>
              {" "}
              <span className="cv-ref__entry-org">— {exp.empresa}</span>
            </>
          )}
        </div>
        <div className="cv-ref__entry-aside">
          {exp.ubicacion && <div className="cv-ref__entry-loc">{exp.ubicacion}</div>}
          {(fechaInicio || fechaFin) && (
            <div className="cv-ref__entry-date">
              {fechaInicio || "?"} – {fechaFin || "Actual"}
            </div>
          )}
        </div>
      </div>
      {exp.responsabilidades.length > 0 && (
        <ul className="cv-ref__bullets">
          {exp.responsabilidades.map((r, j) => (
            <li key={j}>{r}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function SkillRow({ label, values }: { label: string; values: string[] }) {
  if (values.length === 0) return null;
  return (
    <p className="cv-ref__skills-row">
      <span className="cv-ref__skills-label">{label}: </span>
      <span className="cv-ref__skills-val">{values.join(", ")}</span>
    </p>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────

function buildContactLine(meta: CVContext["meta"]): string[] {
  const items: string[] = [];
  if (meta.contacto.telefono.trim()) items.push(meta.contacto.telefono);
  if (meta.contacto.email.trim()) items.push(meta.contacto.email);
  if (meta.contacto.linkedin.trim()) items.push(meta.contacto.linkedin);
  if (meta.contacto.ubicacion.trim()) items.push(meta.contacto.ubicacion);
  return items;
}

function hasAnySkill(s: CVContext["habilidades"]): boolean {
  return Boolean(
    s.tecnicas.length || s.blandas.length || s.idiomas.length || s.tecnologias.length
  );
}

function formatDate(d: string): string {
  const s = d.trim();
  if (!s) return "";
  const parts = s.split("-");
  if (parts.length >= 2) {
    const meses = [
      "ene.", "feb.", "mar.", "abr.", "may.", "jun.",
      "jul.", "ago.", "sep.", "oct.", "nov.", "dic.",
    ];
    const mes = parseInt(parts[1], 10);
    const mesLabel = meses[mes - 1] || parts[1];
    return `${mesLabel} ${parts[0]}`;
  }
  return s;
}
