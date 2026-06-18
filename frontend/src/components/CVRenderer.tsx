import type { CV } from "../lib/supabase";

type CVData = Record<string, unknown>;

function parse(data: CV): CVData | null {
  try {
    return JSON.parse(data.context_json) as CVData;
  } catch {
    return null;
  }
}

function safe<T>(val: unknown, fallback: T): T {
  return (val ?? fallback) as T;
}

function asArray(val: unknown): unknown[] {
  return Array.isArray(val) ? val : [];
}

function asString(val: unknown): string {
  return typeof val === "string" ? val : "";
}

// ── Experience entry helper ──────────────────────────

function formatDate(d: unknown): string {
  const s = asString(d);
  if (!s) return "";
  // try to parse YYYY-MM-DD or YYYY-MM
  const parts = s.split("-");
  if (parts.length >= 2) {
    const meses = [
      "ene.", "feb.", "mar.", "abr.", "may.", "jun.",
      "jul.", "ago.", "sep.", "oct.", "nov.", "dic.",
    ];
    const mes = parseInt(parts[1], 10);
    return `${meses[mes - 1] || parts[1]} ${parts[0]}`;
  }
  return s;
}

function contactItems(meta: unknown): string[] {
  const m = (meta as Record<string, unknown>) ?? {};
  const contacto = (m["contacto"] as Record<string, unknown>) ?? {};
  const items: string[] = [];
  if (contacto["telefono"]) items.push(asString(contacto["telefono"]));
  if (contacto["email"]) items.push(asString(contacto["email"]));
  if (contacto["linkedin"]) items.push(asString(contacto["linkedin"]));
  if (contacto["ubicacion"]) items.push(asString(contacto["ubicacion"]));
  // extra links from recursos_actuales
  const recursos = m["recursos_actuales"] as Record<string, unknown> | undefined;
  if (recursos?.links) {
    const links = asArray(recursos.links);
    for (const link of links) {
      if (typeof link === "string") {
        // add if not already LinkedIn (simple dedup)
        const alreadyLinkedIn = items.some((i) =>
          i.toLowerCase().includes("linkedin")
        );
        if (
          link.toLowerCase().includes("linkedin.com") &&
          alreadyLinkedIn
        )
          continue;
        items.push(link);
      }
    }
  }
  return items;
}

export function CVRenderer({ cv }: { cv: CV }) {
  const data = parse(cv);
  if (!data) {
    return (
      <div className="cv-preview-empty">
        No se pudo parsear el JSON del CV.
      </div>
    );
  }

  const meta = data["meta"] as Record<string, unknown> | undefined;
  const nombre = asString(meta?.["nombre_completo"]);
  const tituloProf = asString(meta?.["titulo_profesional"]);
  const contactLine = contactItems(meta);

  const perfil = data["perfil_profesional"] as Record<string, unknown> | undefined;
  const resumen = asString(perfil?.["resumen"]);

  const experiencia = asArray(data["experiencia"]);
  const educacion = asArray(data["educacion"]);
  const habilidades = data["habilidades"] as Record<string, unknown> | undefined;

  const proyectos = asArray(data["proyectos"]);
  const certificaciones = asArray(data["certificaciones"]);
  const fortalezas = asArray(data["fortalezas"]);

  // section helper
  const Section = ({
    title,
    children,
  }: {
    title: string;
    children: React.ReactNode;
  }) => (
    <div className="cv-ref__section">
      <h2 className="cv-ref__section-title">{title}</h2>
      {children}
    </div>
  );

  return (
    <div className="cv-paper">
      <div className="cv-ref">
        {/* Header */}
        <header className="cv-ref__header">
          {nombre && <h1 className="cv-ref__name">{nombre}</h1>}
          {tituloProf && (
            <p
              style={{
                fontSize: 14,
                color: "#000",
                margin: "2px 0 6px",
              }}
            >
              {tituloProf}
            </p>
          )}
          {contactLine.length > 0 && (
            <p className="cv-ref__contact-line">
              {contactLine.map((item, i) => (
                <span key={i}>
                  {i > 0 && (
                    <span className="cv-ref__sep">|</span>
                  )}
                  <span className="cv-ref__contact-val">{item}</span>
                </span>
              ))}
            </p>
          )}
        </header>

        {/* Perfil Profesional */}
        {resumen && (
          <Section title="Perfil Profesional">
            <p className="cv-ref__para">{resumen}</p>
          </Section>
        )}

        {/* Experiencia */}
        {experiencia.length > 0 && (
          <Section title="Experiencia">
            {experiencia.map((exp, i) => {
              const e = exp as Record<string, unknown>;
              const puesto = asString(e["puesto"]);
              const empresa = asString(e["empresa"]);
              const ubicacion = asString(e["ubicacion"]);
              const fechaInicio = formatDate(e["fecha_inicio"]);
              const fechaFin = formatDate(e["fecha_fin"]);
              const responsabilidades = asArray(e["responsabilidades"]);

              return (
                <div className="cv-ref__entry" key={i}>
                  <div className="cv-ref__entry-head">
                    <div className="cv-ref__entry-main">
                      {puesto && (
                        <span className="cv-ref__entry-role">{puesto}</span>
                      )}
                      {empresa && (
                        <>
                          {" "}
                          <span className="cv-ref__entry-org">— {empresa}</span>
                        </>
                      )}
                    </div>
                    <div className="cv-ref__entry-aside">
                      {ubicacion && (
                        <div className="cv-ref__entry-loc">{ubicacion}</div>
                      )}
                      {(fechaInicio || fechaFin) && (
                        <div className="cv-ref__entry-date">
                          {fechaInicio || "?"} – {fechaFin || "Actual"}
                        </div>
                      )}
                    </div>
                  </div>
                  {responsabilidades.length > 0 && (
                    <ul className="cv-ref__bullets">
                      {responsabilidades.map((r, j) => (
                        <li key={j}>{asString(r)}</li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </Section>
        )}

        {/* Habilidades */}
        {habilidades && (
          <Section title="Habilidades">
            {(() => {
              const tecnicas = asArray(habilidades["tecnicas"]);
              const blandas = asArray(habilidades["blandas"]);
              const idiomas = asArray(habilidades["idiomas"]);
              const tecnologias = asArray(habilidades["tecnologias"]);

              return (
                <>
                  {tecnicas.length > 0 && (
                    <p className="cv-ref__skills-row">
                      <span className="cv-ref__skills-label">Técnicas: </span>
                      <span className="cv-ref__skills-val">
                        {tecnicas.join(", ")}
                      </span>
                    </p>
                  )}
                  {blandas.length > 0 && (
                    <p className="cv-ref__skills-row">
                      <span className="cv-ref__skills-label">
                        Habilidades Blandas:{" "}
                      </span>
                      <span className="cv-ref__skills-val">
                        {blandas.join(", ")}
                      </span>
                    </p>
                  )}
                  {idiomas.length > 0 && (
                    <p className="cv-ref__skills-row">
                      <span className="cv-ref__skills-label">Idiomas: </span>
                      <span className="cv-ref__skills-val">
                        {idiomas.join(", ")}
                      </span>
                    </p>
                  )}
                  {tecnologias.length > 0 && (
                    <p className="cv-ref__skills-row">
                      <span className="cv-ref__skills-label">
                        Tecnologías:{" "}
                      </span>
                      <span className="cv-ref__skills-val">
                        {tecnologias.join(", ")}
                      </span>
                    </p>
                  )}
                </>
              );
            })()}
          </Section>
        )}

        {/* Educación y Certificaciones */}
        {(educacion.length > 0 || certificaciones.length > 0) && (
          <Section title="Educación y Certificaciones">
            {educacion.map((edu, i) => {
              const e = edu as Record<string, unknown>;
              const titulo = asString(e["titulo"]);
              const institucion = asString(e["institucion"]);
              const fechaFin = formatDate(e["fecha_fin"]);
              const desc = asString(e["descripcion"]);

              return (
                <div className="cv-ref__entry" key={`edu-${i}`}>
                  <div className="cv-ref__entry-head">
                    <div className="cv-ref__entry-main">
                      {titulo && (
                        <span className="cv-ref__entry-role">{titulo}</span>
                      )}
                      {institucion && (
                        <>
                          {" "}
                          <span className="cv-ref__entry-org">
                            — {institucion}
                          </span>
                        </>
                      )}
                    </div>
                    <div className="cv-ref__entry-aside">
                      {fechaFin && (
                        <div className="cv-ref__entry-date">{fechaFin}</div>
                      )}
                    </div>
                  </div>
                  {desc && <p className="cv-ref__para">{desc}</p>}
                </div>
              );
            })}
            {certificaciones.length > 0 && (
              <div style={{ marginTop: 8 }}>
                {certificaciones.map((cert, i) => {
                  const c = cert as Record<string, unknown>;
                  return (
                    <p className="cv-ref__para" key={`cert-${i}`}>
                      {asString(c["nombre"])}
                      {c["institucion"]
                        ? ` – ${asString(c["institucion"])}`
                        : ""}
                    </p>
                  );
                })}
              </div>
            )}
          </Section>
        )}

        {/* Proyectos */}
        {proyectos.length > 0 && (
          <Section title="Proyectos">
            {proyectos.map((proj, i) => {
              const p = proj as Record<string, unknown>;
              const nombre = asString(p["nombre"]);
              const rol = asString(p["rol"]);
              const tecnologias = asArray(p["tecnologias"]);
              const url = asString(p["url"]);
              const descripcion = asString(p["descripcion"]);

              return (
                <div className="cv-ref__entry" key={i}>
                  <p className="cv-ref__proj-name">{nombre}</p>
                  <div className="cv-ref__proj-meta">
                    {rol && <span>Rol: {rol}</span>}
                    {tecnologias.length > 0 && (
                      <span>Tecnologías: {tecnologias.join(", ")}</span>
                    )}
                    {url && (
                      <span className="cv-ref__proj-desc">
                        <a
                          className="cv-ref__proj-link-anchor"
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {url}
                        </a>
                      </span>
                    )}
                  </div>
                  {descripcion && (
                    <p
                      className="cv-ref__para"
                      style={{ marginTop: 4 }}
                    >
                      {descripcion}
                    </p>
                  )}
                </div>
              );
            })}
          </Section>
        )}

        {/* Adicional (fortalezas + otros) */}
        {(fortalezas.length > 0) && (
          <Section title="Adicional">
            {fortalezas.map((f, i) => {
              const item = f as Record<string, unknown>;
              return (
                <p className="cv-ref__para" key={i}>
                  {asString(item["nombre"] || item["descripcion"] || "")}
                </p>
              );
            })}
          </Section>
        )}
      </div>
    </div>
  );
}
