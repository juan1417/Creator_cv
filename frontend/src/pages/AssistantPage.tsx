import { useState } from "react";

type Message = { role: "user" | "ai" | "system"; content: string };

const SUGGESTIONS = [
  "Mejorar resumen",
  "Revisar experiencia",
  "Sugerir skills",
  "Optimizar ATS",
  "Revisión completa",
];

export function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "system", content: "Asistente AI conectado. Puedo ayudarte a mejorar cualquier sección de tu CV." },
    { role: "ai", content: "Hola 👋 Soy tu asistente AI para optimización de CVs. Puedo ayudarte con:\n\n• **Mejorar el resumen** profesional\n• **Reescribir descripciones** de experiencia con métricas\n• **Sugerir habilidades** relevantes para tu sector\n• **Optimizar para ATS** (applicant tracking systems)\n• **Revisar la estructura** completa del CV\n\n¿Qué sección quieres que revise?" },
  ]);
  const [input, setInput] = useState("");

  const sendMessage = (text?: string) => {
    const content = text || input.trim();
    if (!content) return;
    setMessages((prev) => [...prev, { role: "user", content }, { role: "ai", content: "Estoy analizando tu solicitud. Un momento por favor…" }]);
    setInput("");
  };

  return (
    <>
      <div className="topbar">
        <div className="topbar-left">
          <div className="topbar-title">Asistente AI</div>
        </div>
      </div>
      <div className="ai-layout">
      <div className="conversation-panel">
        <div className="conversation-header">
          <div className="conversation-title">
            Agente AI
            <span className="ai-status"><span className="ai-status-dot" />En línea</span>
          </div>
        </div>

        <div className="conversation-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`msg msg-${msg.role}`}>{msg.content}</div>
          ))}
          <div className="suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="suggestion-chip" onClick={() => sendMessage(s)}>{s}</button>
            ))}
          </div>
        </div>

        <div className="conversation-input">
          <div className="input-row">
            <div className="input-wrap">
              <textarea
                placeholder="Preguntale algo al agente AI…"
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
              />
            </div>
            <button className="send-btn" onClick={() => sendMessage()}>→</button>
          </div>
        </div>
      </div>

      <div className="tools-panel">
        <div className="tools-panel-header">Herramientas</div>

        <div className="active-cv">
          <div className="active-cv-icon">📄</div>
          <div>
            <div className="active-cv-info">Sin CV seleccionado</div>
            <div className="active-cv-detail">Seleccioná un CV para empezar</div>
          </div>
        </div>

        <div className="tools-list">
          <div className="tool-item">
            <div className="tool-item-icon">✨</div>
            <div className="tool-item-info">
              <div className="tool-item-name">Mejorar con AI</div>
              <div className="tool-item-desc">Reescribe y optimiza secciones</div>
            </div>
          </div>
          <div className="tool-item">
            <div className="tool-item-icon">🔍</div>
            <div className="tool-item-info">
              <div className="tool-item-name">Revisión ATS</div>
              <div className="tool-item-desc">Analiza compatibilidad con parsers</div>
            </div>
          </div>
          <div className="tool-item">
            <div className="tool-item-icon">📊</div>
            <div className="tool-item-info">
              <div className="tool-item-name">Comparar con oferta</div>
              <div className="tool-item-desc">Evalúa contra una oferta laboral</div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </>
  );
}
