import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { apiGetCV, type CV } from "../lib/api";
import { CVRenderer } from "../components/CVRenderer";
import { parseContext } from "../types/cv";
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, TabStopPosition, TabStopType, BorderStyle, convertInchesToTwip } from "docx";

export function PreviewPage() {
  const { id } = useParams<{ id: string }>();
  const [cv, setCV] = useState<CV | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState<string | null>(null);
  const paperRef = useRef<HTMLDivElement>(null);

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
    void load();
  }, [load]);

  const handleExportPDF = async () => {
    const el = paperRef.current?.querySelector(".cv-paper");
    if (!el) return;
    setExporting("pdf");
    try {
      const html2canvas = (await import("html2canvas")).default;
      const { jsPDF } = await import("jspdf");

      const canvas = await html2canvas(el as HTMLElement, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: "#ffffff",
      });

      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfW = pdf.internal.pageSize.getWidth();
      const pdfH = pdf.internal.pageSize.getHeight();
      const imgW = canvas.width;
      const imgH = canvas.height;
      const ratio = Math.min(pdfW / imgW, pdfH / imgH);

      pdf.addImage(imgData, "PNG", 0, 0, imgW * ratio, imgH * ratio);
      pdf.save(`${cv?.title ?? "CV"}.pdf`);
    } catch (e) {
      setError(`Error al exportar PDF: ${String(e)}`);
    } finally {
      setExporting(null);
    }
  };

  const handleExportDOCX = async () => {
    if (!cv) return;
    setExporting("docx");
    try {
      const data = parseContext(cv.context_json);
      const m = data.meta;
      const vs = data.settings?.visibleSections;

      const children: InstanceType<typeof Paragraph>[] = [];

      // Header
      if (m.nombre_completo) {
        children.push(new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: m.nombre_completo, bold: true, size: 28, font: "Calibri" })],
        }));
      }
      if (m.titulo_profesional) {
        children.push(new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: m.titulo_profesional, size: 22, color: "666666", font: "Calibri" })],
        }));
      }

      // Contact line
      const contactParts: string[] = [];
      if (m.contacto.email) contactParts.push(m.contacto.email);
      if (m.contacto.telefono) contactParts.push(m.contacto.telefono);
      if (m.contacto.linkedin) contactParts.push(m.contacto.linkedin);
      if (m.contacto.ubicacion) contactParts.push(m.contacto.ubicacion);
      if (contactParts.length > 0) {
        children.push(new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          children: [new TextRun({ text: contactParts.join(" | "), size: 18, font: "Calibri" })],
        }));
      }

      // Separator
      children.push(new Paragraph({
        spacing: { after: 200 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "CCCCCC" } },
        children: [],
      }));

      const show = (key: string) => !vs || vs[key] !== false;

      // Perfil
      if (show("summary") && m.objetivo_cv) {
        children.push(sectionHeading("PERFIL PROFESIONAL"));
        children.push(new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: m.objetivo_cv, size: 20, font: "Calibri" })],
        }));
      }

      // Experiencia
      if (show("experience") && data.experiencia.length > 0) {
        children.push(sectionHeading("EXPERIENCIA"));
        for (const exp of data.experiencia) {
          const roleLine = [exp.puesto, exp.empresa].filter(Boolean).join(" — ");
          const dateRange = [exp.fecha_inicio, exp.fecha_fin].filter(Boolean).join(" - ");
          children.push(new Paragraph({
            spacing: { before: 120, after: 40 },
            children: [new TextRun({ text: roleLine, bold: true, size: 20, font: "Calibri" })],
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
          }));
          if (dateRange) {
            children.push(new Paragraph({
              spacing: { after: 40 },
              children: [new TextRun({ text: dateRange, size: 18, color: "666666", font: "Calibri" })],
            }));
          }
          for (const r of exp.responsabilidades) {
            if (!r) continue;
            children.push(new Paragraph({
              spacing: { after: 40 },
              indent: { left: convertInchesToTwip(0.25) },
              children: [new TextRun({ text: `• ${r}`, size: 20, font: "Calibri" })],
            }));
          }
        }
      }

      // Habilidades
      if (show("skills") && (data.habilidades.tecnicas.length || data.habilidades.blandas.length || data.habilidades.idiomas.length || data.habilidades.tecnologias.length)) {
        children.push(sectionHeading("HABILIDADES"));
        const addSkillRow = (label: string, vals: string[]) => {
          if (vals.length === 0) return;
          children.push(new Paragraph({
            spacing: { after: 60 },
            children: [
              new TextRun({ text: `${label}: `, bold: true, size: 20, font: "Calibri" }),
              new TextRun({ text: vals.join(", "), size: 20, font: "Calibri" }),
            ],
          }));
        };
        addSkillRow("Técnicas", data.habilidades.tecnicas);
        addSkillRow("Habilidades Blandas", data.habilidades.blandas);
        addSkillRow("Idiomas", data.habilidades.idiomas);
        addSkillRow("Tecnologías", data.habilidades.tecnologias);
      }

      // Educación
      if (show("education") && data.educacion.length > 0) {
        children.push(sectionHeading("EDUCACIÓN"));
        for (const edu of data.educacion) {
          const titleLine = [edu.titulo, edu.institucion].filter(Boolean).join(" — ");
          children.push(new Paragraph({
            spacing: { before: 120, after: 40 },
            children: [new TextRun({ text: titleLine, bold: true, size: 20, font: "Calibri" })],
          }));
          if (edu.fecha_fin) {
            children.push(new Paragraph({
              spacing: { after: 40 },
              children: [new TextRun({ text: edu.fecha_fin, size: 18, color: "666666", font: "Calibri" })],
            }));
          }
          if (edu.descripcion) {
            children.push(new Paragraph({
              spacing: { after: 40 },
              children: [new TextRun({ text: edu.descripcion, size: 20, font: "Calibri" })],
            }));
          }
        }
      }

      // Certificaciones
      if (data.certificaciones.length > 0) {
        children.push(sectionHeading("CERTIFICACIONES"));
        for (const cert of data.certificaciones) {
          const parts = [cert.nombre, cert.institucion, cert.fecha].filter(Boolean).join(" — ");
          children.push(new Paragraph({
            spacing: { after: 60 },
            children: [new TextRun({ text: parts, size: 20, font: "Calibri" })],
          }));
        }
      }

      // Proyectos
      if (show("projects") && data.proyectos.length > 0) {
        children.push(sectionHeading("PROYECTOS"));
        for (const proj of data.proyectos) {
          children.push(new Paragraph({
            spacing: { before: 120, after: 40 },
            children: [new TextRun({ text: proj.nombre, bold: true, size: 20, font: "Calibri" })],
          }));
          const meta = [proj.rol, proj.tecnologias.join(", ")].filter(Boolean).join(" | ");
          if (meta) {
            children.push(new Paragraph({
              spacing: { after: 40 },
              children: [new TextRun({ text: meta, size: 18, color: "666666", font: "Calibri" })],
            }));
          }
          if (proj.descripcion) {
            children.push(new Paragraph({
              spacing: { after: 40 },
              children: [new TextRun({ text: proj.descripcion, size: 20, font: "Calibri" })],
            }));
          }
        }
      }

      const doc = new Document({
        sections: [{
          properties: {
            page: {
              margin: { top: convertInchesToTwip(0.8), bottom: convertInchesToTwip(0.8), left: convertInchesToTwip(1), right: convertInchesToTwip(1) },
            },
          },
          children,
        }],
      });

      const blob = await Packer.toBlob(doc);
      downloadBlob(blob, `${cv.title ?? "CV"}.docx`);
    } catch (e) {
      setError(`Error al exportar DOCX: ${String(e)}`);
    } finally {
      setExporting(null);
    }
  };

  const handleExportTXT = () => {
    if (!cv) return;
    setExporting("txt");
    try {
      const data = parseContext(cv.context_json);
      const m = data.meta;
      const vs = data.settings?.visibleSections;
      const lines: string[] = [];

      const show = (key: string) => !vs || vs[key] !== false;

      if (m.nombre_completo) lines.push(m.nombre_completo);
      if (m.titulo_profesional) lines.push(m.titulo_profesional);

      const contact: string[] = [];
      if (m.contacto.email) contact.push(m.contacto.email);
      if (m.contacto.telefono) contact.push(m.contacto.telefono);
      if (m.contacto.linkedin) contact.push(m.contacto.linkedin);
      if (m.contacto.ubicacion) contact.push(m.contacto.ubicacion);
      if (contact.length) lines.push(contact.join(" | "));
      lines.push("");

      if (show("summary") && m.objetivo_cv) {
        lines.push("=== PERFIL PROFESIONAL ===");
        lines.push(m.objetivo_cv);
        lines.push("");
      }

      if (show("experience") && data.experiencia.length) {
        lines.push("=== EXPERIENCIA ===");
        for (const exp of data.experiencia) {
          const dates = [exp.fecha_inicio, exp.fecha_fin].filter(Boolean).join(" - ");
          lines.push(`${[exp.puesto, exp.empresa].filter(Boolean).join(" — ")}${dates ? ` (${dates})` : ""}`);
          for (const r of exp.responsabilidades) {
            if (r) lines.push(`  • ${r}`);
          }
        }
        lines.push("");
      }

      if (show("skills")) {
        const h = data.habilidades;
        const addRow = (label: string, vals: string[]) => { if (vals.length) lines.push(`${label}: ${vals.join(", ")}`); };
        if (h.tecnicas.length || h.blandas.length || h.idiomas.length || h.tecnologias.length) {
          lines.push("=== HABILIDADES ===");
          addRow("Técnicas", h.tecnicas);
          addRow("Blandas", h.blandas);
          addRow("Idiomas", h.idiomas);
          addRow("Tecnologías", h.tecnologias);
          lines.push("");
        }
      }

      if (show("education") && data.educacion.length) {
        lines.push("=== EDUCACIÓN ===");
        for (const edu of data.educacion) {
          lines.push([edu.titulo, edu.institucion].filter(Boolean).join(" — "));
          if (edu.fecha_fin) lines.push(`  ${edu.fecha_fin}`);
          if (edu.descripcion) lines.push(`  ${edu.descripcion}`);
        }
        lines.push("");
      }

      if (data.certificaciones.length) {
        lines.push("=== CERTIFICACIONES ===");
        for (const c of data.certificaciones) {
          lines.push([c.nombre, c.institucion, c.fecha].filter(Boolean).join(" — "));
        }
        lines.push("");
      }

      if (show("projects") && data.proyectos.length) {
        lines.push("=== PROYECTOS ===");
        for (const p of data.proyectos) {
          lines.push(p.nombre);
          if (p.rol || p.tecnologias.length) lines.push(`  ${[p.rol, p.tecnologias.join(", ")].filter(Boolean).join(" | ")}`);
          if (p.descripcion) lines.push(`  ${p.descripcion}`);
        }
      }

      const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
      downloadBlob(blob, `${cv.title ?? "CV"}.txt`);
    } finally {
      setExporting(null);
    }
  };

  return (
    <>
      {/* Topbar */}
      <div className="topbar">
        <div className="topbar-left">
          <Link to={`/cv/${id}`} className="topbar-back" aria-label="Volver al editor">←</Link>
          <div className="topbar-title">{cv?.title ?? "Vista previa"}</div>
        </div>
        <div className="topbar-actions">
          {cv && (
            <>
              <button
                type="button"
                className="btn btn-primary"
                style={{ fontSize: 12, padding: "5px 12px" }}
                onClick={handleExportPDF}
                disabled={exporting !== null}
              >
                {exporting === "pdf" ? "Exportando…" : "PDF"}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: 12, padding: "5px 12px" }}
                onClick={handleExportDOCX}
                disabled={exporting !== null}
              >
                {exporting === "docx" ? "Exportando…" : "Word"}
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                style={{ fontSize: 12, padding: "5px 12px" }}
                onClick={handleExportTXT}
                disabled={exporting !== null}
              >
                {exporting === "txt" ? "Exportando…" : "TXT"}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Preview Container */}
      <div className="preview-container">
        {loading && <p className="empty-state" style={{ padding: 32 }}>Cargando…</p>}
        {error && (
          <div className="flash flash-error" style={{ margin: 24 }}>{error}</div>
        )}

        {cv && (
          <div className="preview-scroll">
            <div className="preview-page" ref={paperRef}>
              <CVRenderer cv={cv} />
            </div>
          </div>
        )}
      </div>
    </>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────

function sectionHeading(text: string) {
  return new Paragraph({
    spacing: { before: 200, after: 100 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC" } },
    children: [new TextRun({ text, bold: true, size: 20, font: "Calibri", color: "333333" })],
  });
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
