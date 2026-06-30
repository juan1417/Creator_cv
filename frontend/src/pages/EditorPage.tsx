import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { apiGetCV, apiUpdateCV, apiChatAI, apiGetChat, apiClearChat, type CV, type CVPatch } from "../lib/api";
import { parseContext, emptyContext, type CVContext, type CVSettings } from "../types/cv";
import { CVRenderer } from "../components/CVRenderer";
import { useDebouncedAutoSave, type SaveStatus } from "../hooks/useDebouncedAutoSave";
import { HeaderSection } from "../components/editor/sections/HeaderSection";
import { ExperienceSection } from "../components/editor/sections/ExperienceSection";
import { EducationSection } from "../components/editor/sections/EducationSection";
import { SkillsSection } from "../components/editor/sections/SkillsSection";
import { ProjectsSection } from "../components/editor/sections/ProjectsSection";
import { AdditionalSection } from "../components/editor/sections/AdditionalSection";
import { TEMPLATES } from "../lib/cv-templates";

const COLORS = ["#0071e3", "#000000", "#6e6e73", "#34c759", "#ff9500", "#ff3b30", "#af52de", "#5856d6"];

const FONTS = [
  { value: "system", label: "Sistema (SF Pro)" },
  { value: "georgia", label: "Georgia (Serif)" },
  { value: "garamond", label: "Garamond (Serif)" },
  { value: "helvetica", label: "Helvetica" },
];

const SECTIONS = [
  { key: "summary", label: "Resumen profesional" },
  { key: "experience", label: "Experiencia laboral" },
  { key: "education", label: "Educación" },
  { key: "skills", label: "Habilidades" },
  { key: "projects", label: "Proyectos" },
];

type AiMsg = { role: "ai" | "user" | "system"; content: string; patches?: CVPatch[] };

export function EditorPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [cv, setCV] = useState<CV | null>(null);
  const [title, setTitle] = useState("");
  const [ctx, setCtx] = useState<CVContext>(emptyContext);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"editor" | "preview" | "settings">("editor");

  // Settings — derived from ctx.settings (persisted in context_json)
  const settings: CVSettings = ctx.settings;
  const updateSettings = (patch: Partial<CVSettings>) =>
    setCtx((p) => ({ ...p, settings: { ...p.settings, ...patch } }));
  const updateVisibleSections = (key: string) =>
    updateSettings({ visibleSections: { ...settings.visibleSections, [key]: !settings.visibleSections[key] } });

  const [previewZoom, setPreviewZoom] = useState(1);

  // AI Panel
  const [aiMessages, setAiMessages] = useState<AiMsg[]>([]);
  const [aiInput, setAiInput] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const aiEndRef = useRef<HTMLDivElement>(null);

  // Load chat history on mount
  useEffect(() => {
    if (!id) return;
    apiGetChat(id).then((msgs) => {
      if (msgs.length > 0) {
        setAiMessages(msgs.map((m) => ({ role: m.role === "assistant" ? "ai" : m.role as "user" | "ai", content: m.content })));
      } else {
        setAiMessages([
          { role: "system", content: "Asistente ATS conectado. Puedo ayudarte a optimizar tu CV para sistemas de seguimiento de candidatos." },
          { role: "ai", content: "Hola! Soy tu asistente especializado en optimizar CVs para ATS (Applicant Tracking Systems). Puedo:\n\n• **Analizar tu CV** para detectar problemas con ATS\n• **Sugerir keywords** que los buscan los reclutadores\n• **Mejorar tu resumen** profesional con verbos de accion\n• **Reescribir experiencias** con metricas concretas\n• **Revisar formato** para maxima compatibilidad\n\nQue seccion queres que revise primero?" },
        ]);
      }
    }).catch(() => {
      setAiMessages([
        { role: "system", content: "Asistente ATS conectado." },
        { role: "ai", content: "Hola! Puedo ayudarte a optimizar tu CV para ATS. Que seccion queres que revise?" },
      ]);
    });
  }, [id]);

  // Auto-scroll on new messages
  useEffect(() => {
    aiEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [aiMessages]);

  const applyPatch = (patch: CVPatch) => {
    setCtx((prev) => {
      const next = { ...prev } as Record<string, unknown>;
      const section = patch.section as string;
      const target = next[section];
      if (target && typeof target === "object" && !Array.isArray(target)) {
        (target as Record<string, unknown>)[patch.field] = patch.value;
      } else if (Array.isArray(target)) {
        const arr = [...target];
        if (patch.action === "update" && typeof patch.index === "number" && arr[patch.index]) {
          (arr[patch.index] as Record<string, unknown>)[patch.field] = patch.value;
        } else if (patch.action === "add") {
          arr.push({ [patch.field]: patch.value });
        } else if (patch.action === "remove" && typeof patch.index === "number") {
          arr.splice(patch.index, 1);
        }
        next[section] = arr;
      }
      return next as unknown as CVContext;
    });
    showToast("Cambio aplicado al CV");
  };

  const sendAi = async () => {
    const text = aiInput.trim();
    if (!text || !id || aiLoading) return;
    setAiMessages((prev) => [...prev, { role: "user", content: text }]);
    setAiInput("");
    setAiLoading(true);
    try {
      const result = await apiChatAI(id, text);
      setAiMessages((prev) => [...prev, { role: "ai", content: result.response, patches: result.patches.length > 0 ? result.patches : undefined }]);
    } catch {
      setAiMessages((prev) => [...prev, { role: "ai", content: "Error al conectar con la IA. Verifica que la API key de Gemini esté configurada." }]);
    } finally {
      setAiLoading(false);
    }
  };

  const ATS_SUGGESTIONS = [
    { label: "Analizar ATS", message: "Analiza mi CV completo para ATS y dame un score de compatibilidad. Identifica problemas de formato y keywords faltantes." },
    { label: "Sugerir keywords", message: "Que keywords deberia agregar a mi CV para mejorar el matching con ofertas de mi sector? Dame una lista concreta." },
    { label: "Mejorar resumen", message: "Reescribi mi perfil profesional con verbos de accion, metricas y keywords relevantes para ATS. Mantene maximo 3 lineas." },
    { label: "Mejorar experiencia", message: "Reescribi mi experiencia laboral con verbos de accion al inicio de cada bullet, metricas concretas y keywords tecnicas." },
    { label: "Revisar formato", message: "Revisa si mi CV tiene problemas de formato para ATS: tablas, columnas, fuentes incompatibles, fechas inconsistentes." },
  ];

  const load = useCallback(async () => {
    if (!id) return;
    // Check localStorage backup first (fast, synchronous)
    const backupRaw = localStorage.getItem(`cv_draft_${id}`);
    if (backupRaw) {
      try {
        const backup = JSON.parse(backupRaw) as CVContext;
        setCtx(backup);
        // Still fetch CV metadata (title, etc.) but don't overwrite context
        const data = await apiGetCV(id);
        setCV(data);
        setTitle(data.title);
        setLoading(false);
        return;
      } catch { /* corrupted backup, fall through */ }
    }
    try {
      const data = await apiGetCV(id);
      setCV(data);
      setTitle(data.title);
      setCtx(parseContext(data.context_json));
    } catch (e: unknown) {
      setError(`Error: ${String(e)}`);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { void load(); }, [load]);

  const ctxJson = useMemo(() => JSON.stringify(ctx, null, 2), [ctx]);

  const save = useCallback(async () => {
    if (!id) return;
    await apiUpdateCV(id, { context_json: ctxJson });
  }, [id, ctxJson]);

  const storageKey = id ? `cv_draft_${id}` : undefined;
  const { status: saveStatus, error: saveError, flush } = useDebouncedAutoSave({
    value: ctx,
    save,
    storageKey,
    delay: 800,
  });

  // Save before tab close / refresh
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (saveStatus === "pending" || saveStatus === "saving") {
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [saveStatus]);

  const handleBack = async () => {
    if (saveStatus === "pending" || saveStatus === "saving") {
      await flush();
    }
    navigate("/");
  };

  const handleTitleBlur = async () => {
    if (!id || !title.trim()) return;
    try { await apiUpdateCV(id, { title: title.trim() }); } catch { /* */ }
  };

  if (loading) return <div className="content"><p className="empty-state">Cargando CV…</p></div>;
  if (!cv) return <div className="content"><p className="empty-state">CV no encontrado.</p><Link to="/" className="btn btn-primary">Volver</Link></div>;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Topbar */}
      <div className="topbar">
        <div className="topbar-left">
          <button type="button" className="topbar-back" onClick={handleBack}>←</button>
          <div className="topbar-title">{cv.title}</div>
        </div>
        <div className="topbar-actions">
          <span className={`save-indicator save-indicator--${saveStatus}`}><SaveLabel status={saveStatus} /></span>
          <button className="btn btn-secondary" style={{ fontSize: 12, padding: "5px 12px" }} onClick={() => showToast("Borrador guardado")}>Guardar borrador</button>
          <button className="btn btn-primary" style={{ fontSize: 12, padding: "5px 12px" }} onClick={() => showToast("CV exportado como PDF")}>Exportar PDF</button>
        </div>
      </div>

      {/* Editor Tabs */}
      <div className="editor-tabs" role="tablist">
        {(["editor", "preview", "settings"] as const).map((tab) => (
          <button key={tab} className={`editor-tab${activeTab === tab ? " active" : ""}`} role="tab" aria-selected={activeTab === tab} onClick={() => setActiveTab(tab)}>
            {tab === "editor" ? "Editor" : tab === "preview" ? "Vista previa" : "Configuración"}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="editor-layout">
        {/* Main content */}
        <div style={{ display: "flex", flexDirection: "column", flex: 1, minWidth: 0, overflow: "hidden" }}>
          {/* ─── EDITOR TAB ─── */}
          {activeTab === "editor" && (
            <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>
              {error && <div className="flash flash-error" style={{ marginBottom: 16 }}>{error}</div>}
              {saveError && <div className="flash flash-error" style={{ marginBottom: 16 }}>Error al guardar: {saveError}</div>}

              <HeaderSection value={ctx.meta} onChange={(meta) => setCtx((p) => ({ ...p, meta }))} />
              <ExperienceSection value={ctx.experiencia} onChange={(experiencia) => setCtx((p) => ({ ...p, experiencia }))} />
              <EducationSection value={ctx.educacion} onChange={(educacion) => setCtx((p) => ({ ...p, educacion }))} />
              <SkillsSection value={ctx.habilidades} onChange={(habilidades) => setCtx((p) => ({ ...p, habilidades }))} />
              <ProjectsSection value={ctx.proyectos} onChange={(proyectos) => setCtx((p) => ({ ...p, proyectos }))} />
              <AdditionalSection
                certificaciones={ctx.certificaciones}
                fortalezas={ctx.fortalezas}
                onChangeCertificaciones={(certificaciones) => setCtx((p) => ({ ...p, certificaciones }))}
                onChangeFortalezas={(fortalezas) => setCtx((p) => ({ ...p, fortalezas }))}
              />
            </div>
          )}

          {/* ─── PREVIEW TAB ─── */}
          {activeTab === "preview" && (
            <div className="preview-container">
              <div className="preview-toolbar">
                <div className="preview-toolbar-left">
                  <span className="preview-label">Vista previa del CV</span>
                </div>
                <div className="preview-toolbar-right">
                  {([0.8, 1, 1.2] as const).map((z) => (
                    <button key={z} className={`btn btn-secondary${previewZoom === z ? " btn-primary" : ""}`} style={{ fontSize: 12, padding: "5px 12px" }} onClick={() => setPreviewZoom(z)}>
                      {z === 0.8 ? "Pequeño" : z === 1 ? "Normal" : "Grande"}
                    </button>
                  ))}
                </div>
              </div>
              <div className="preview-scroll">
                <div className="preview-page" style={{ transform: `scale(${previewZoom})` }}>
                  <CVRenderer cv={{ ...cv, context_json: ctxJson }} settings={settings} />
                </div>
              </div>
            </div>
          )}

          {/* ─── SETTINGS TAB ─── */}
          {activeTab === "settings" && (
            <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>
              <div className="settings-container">
                {/* Template */}
                <div className="section-group">
                  <div className="section-group-header"><div className="section-group-title">Plantilla</div></div>
                  <div className="section-card">
                    <div className="template-grid">
                      {Object.values(TEMPLATES).map((t) => (
                        <div key={t.id} className={`template-card${settings.template === t.id ? " active" : ""}`} onClick={() => updateSettings({ template: t.id as CVSettings["template"] })}>
                          <div className="template-preview">
                            <div className="tp-minimal">
                              <div className="tp-bar tp-bar-full" />
                              <div className="tp-lines"><div className="tp-line" /><div className="tp-line tp-line-short" /></div>
                              <div className="tp-divider" />
                              <div className="tp-lines"><div className="tp-line" /><div className="tp-line" /><div className="tp-line tp-line-short" /></div>
                            </div>
                          </div>
                          <div className="template-name">{t.name}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Colors */}
                <div className="section-group">
                  <div className="section-group-header"><div className="section-group-title">Color de acento</div></div>
                  <div className="section-card">
                    <div className="color-grid">
                      {COLORS.map((c) => (
                        <button key={c} className={`color-swatch${settings.accentColor === c ? " active" : ""}`} style={{ "--sw": c } as React.CSSProperties} onClick={() => updateSettings({ accentColor: c })} aria-label={c} />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Typography */}
                <div className="section-group">
                  <div className="section-group-header"><div className="section-group-title">Tipografía</div></div>
                  <div className="section-card">
                    <div className="form-group">
                      <label className="form-label">Fuente del título</label>
                      <select className="form-input" value={settings.fontFamily} onChange={(e) => updateSettings({ fontFamily: e.target.value })}>
                        {FONTS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Tamaño base</label>
                      <select className="form-input" value={settings.fontSize} onChange={(e) => updateSettings({ fontSize: Number(e.target.value) })}>
                        <option value={13}>Pequeño (13px)</option>
                        <option value={14}>Normal (14px)</option>
                        <option value={15}>Grande (15px)</option>
                        <option value={16}>Extra grande (16px)</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Interlineado</label>
                      <select className="form-input" value={settings.lineHeight} onChange={(e) => updateSettings({ lineHeight: Number(e.target.value) })}>
                        <option value={1.4}>Compacto</option>
                        <option value={1.5}>Normal</option>
                        <option value={1.6}>Espaciado</option>
                        <option value={1.8}>Amplio</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Section toggles */}
                <div className="section-group">
                  <div className="section-group-header"><div className="section-group-title">Secciones visibles</div></div>
                  <div className="section-card">
                    <div className="section-toggles">
                      {SECTIONS.map((s) => (
                        <label key={s.key} className="section-toggle">
                          <input type="checkbox" checked={settings.visibleSections[s.key]} onChange={() => updateVisibleSections(s.key)} />
                          <span className="toggle-slider" />
                          <span className="toggle-label">{s.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Export */}
                <div className="section-group">
                  <div className="section-group-header"><div className="section-group-title">Exportar</div></div>
                  <div className="section-card">
                    <div className="export-options">
                      <button className="export-btn" onClick={() => showToast("Exportando como PDF...")}>
                        <span className="export-icon">📄</span>
                        <div><span className="export-text">PDF</span><span className="export-desc">Documento listo para imprimir</span></div>
                      </button>
                      <button className="export-btn" onClick={() => showToast("Exportando como DOCX...")}>
                        <span className="export-icon">📝</span>
                        <div><span className="export-text">Word</span><span className="export-desc">Editable en Microsoft Word</span></div>
                      </button>
                      <button className="export-btn" onClick={() => showToast("Exportando como TXT...")}>
                        <span className="export-icon">📃</span>
                        <div><span className="export-text">Texto plano</span><span className="export-desc">ATS-friendly</span></div>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ─── AI PANEL (always visible) ─── */}
        <div className="ai-panel">
          <div className="ai-panel-header">
            <div className="ai-panel-title">Asistente ATS <span className="ai-panel-badge">Gemini</span></div>
            <button className="btn btn-secondary" style={{ fontSize: 12, padding: "5px 12px" }} onClick={() => { setAiMessages([]); if (id) apiClearChat(id).catch(() => {}); }}>Limpiar</button>
          </div>
          <div className="ai-messages">
            {aiMessages.map((m, i) => (
              <div key={i} className={`ai-msg ai-msg-${m.role}`}>
                <div dangerouslySetInnerHTML={{ __html: formatAiMessage(m.content) }} />
                {m.patches && m.patches.length > 0 && (
                  <div className="ai-patches">
                    {m.patches.map((p, j) => (
                      <button key={j} className="btn btn-primary" style={{ fontSize: 11, padding: "4px 10px", marginTop: 4 }} onClick={() => applyPatch(p)}>
                        Aplicar: {p.section}.{p.field}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {aiLoading && (
              <div className="ai-msg ai-msg-ai ai-msg-loading">
                <span className="ai-typing"><span /><span /><span /></span> Analizando...
              </div>
            )}
            <div ref={aiEndRef} />
          </div>
          {aiMessages.length <= 2 && (
            <div className="ai-suggestions">
              {ATS_SUGGESTIONS.map((s) => (
                <button key={s.label} className="ai-suggestion" onClick={() => { setAiInput(s.message); }}>
                  {s.label}
                </button>
              ))}
            </div>
          )}
          <div className="ai-input-wrap">
            <textarea className="ai-input" placeholder="Preguntale al asistente ATS..." rows={1} value={aiInput} onChange={(e) => setAiInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendAi(); } }} disabled={aiLoading} />
            <button className="ai-send" onClick={sendAi} disabled={aiLoading || !aiInput.trim()}>→</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function SaveLabel({ status }: { status: SaveStatus }) {
  switch (status) {
    case "idle": return null;
    case "pending": return <>Pendiente…</>;
    case "saving": return <>Guardando…</>;
    case "saved": return <>Guardado ✓</>;
    case "error": return <>Error al guardar</>;
  }
}

function formatAiMessage(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>")
    .replace(/^- (.*)/gm, "• $1")
    .replace(/^(\d+)\. (.*)/gm, "$1. $2");
}

function showToast(msg: string) {
  const t = document.createElement("div");
  t.className = "toast";
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.classList.add("hide"), 2200);
  setTimeout(() => t.remove(), 2500);
}
