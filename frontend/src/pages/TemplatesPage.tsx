import { useNavigate } from "react-router-dom";
import { apiCreateCV } from "../lib/api";
import { TEMPLATES, type TemplateId } from "../lib/cv-templates";

export function TemplatesPage() {
  const navigate = useNavigate();

  async function handleUseTemplate(id: TemplateId) {
    const tpl = TEMPLATES[id];
    const cv = await apiCreateCV(tpl.name, JSON.stringify(tpl.context));
    navigate(`/editor/${cv.id}`);
  }

  return (
    <>
      <div className="topbar">
        <div className="topbar-left">
          <div className="topbar-title">Plantillas</div>
        </div>
      </div>
      <div className="content">
        <div className="content-header">
          <h1>Plantillas</h1>
          <p>Elegí una plantilla para empezar tu CV.</p>
        </div>

        <div className="template-grid">
          {Object.values(TEMPLATES).map((tpl) => (
            <div key={tpl.id} className="template-card">
              <div className="template-preview">
                <div className="template-mini">
                  <div className="tp-name-bar" />
                  <div className="tp-role-bar" />
                  <div className="tp-section-title" />
                  <div className="tp-line" /><div className="tp-line" /><div className="tp-line" style={{ width: "60%" }} />
                  <div className="tp-section-title" />
                  <div className="tp-line" /><div className="tp-line" style={{ width: "80%" }} />
                </div>
              </div>
              <div className="template-info">
                <h3 className="template-name">{tpl.name}</h3>
                <p className="template-desc">{tpl.description}</p>
                <div className="template-tags">
                  {tpl.tags.map((t) => (
                    <span key={t} className="template-tag">{t}</span>
                  ))}
                </div>
                <div className="template-actions">
                  <button
                    className="btn btn-primary"
                    style={{ flex: 1 }}
                    onClick={() => handleUseTemplate(tpl.id)}
                  >
                    Usar plantilla
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
