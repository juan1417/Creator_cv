// Wrapper simple alrededor de marked.js para mostrar Markdown de forma segura.

const MarkdownLib = (() => {
  if (window.marked && window.marked.setOptions) {
    window.marked.setOptions({ breaks: false, gfm: true });
  }
  function render(md) {
    if (!window.marked) return Shared.escapeHtml(md || "");
    try {
      return window.marked.parse(md || "");
    } catch (e) {
      console.warn("marked falló:", e);
      return Shared.escapeHtml(md || "");
    }
  }
  return { render };
})();

window.MarkdownLib = MarkdownLib;
