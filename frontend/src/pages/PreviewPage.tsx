import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { apiGetCV, type CV } from "../lib/api";
import { CVRenderer } from "../components/CVRenderer";

export function PreviewPage() {
  const { id } = useParams<{ id: string }>();
  const [cv, setCV] = useState<CV | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);
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
    setExporting(true);
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
      setExporting(false);
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
            <button
              type="button"
              className="btn btn-primary"
              style={{ fontSize: 12, padding: "5px 12px" }}
              onClick={handleExportPDF}
              disabled={exporting}
            >
              {exporting ? "Exportando…" : "Exportar PDF"}
            </button>
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
