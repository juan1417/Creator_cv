// Job fit (client-side): extrae términos de la oferta y los cruza con el CV.

(function () {
  const id = Shared.getCvId();
  if (!id) { Shared.flash("Falta el id del CV.", "error"); return; }
  const cv = CvStore.get(id);
  if (!cv) { Shared.flash("No se encontró el CV.", "error"); return; }

  document.getElementById("back-link").href = `/cvs/${encodeURIComponent(id)}/edit`;
  document.getElementById("bc-edit").href = `/cvs/${encodeURIComponent(id)}/edit`;
  document.title = `Compatibilidad · ${cv.title || "CV"}`;

  // Restore last job text
  const key = `jobfit:${id}`;
  const jobText = document.getElementById("job_text");
  jobText.value = Storage.get(key, "") || "";

  const form = document.getElementById("jobfit-form");
  const results = document.getElementById("results");
  const scoreEl = document.getElementById("score");
  const jobTermsEl = document.getElementById("job-terms");
  const cvTermsEl = document.getElementById("cv-terms");
  const missTermsEl = document.getElementById("miss-terms");

  const STOPWORDS = new Set([
    "a","al","algo","algunas","algunos","ante","antes","como","con","contra","cual","cuando","de","del","desde","donde","durante","e","el","ella","ellas","ellos","en","entre","era","erais","eran","eras","eres","es","esa","esas","ese","eso","esos","esta","estaba","estabais","estaban","estabas","estad","estada","estadas","estado","estados","estais","estamos","estan","estar","estará","estarán","estarás","estaré","estaréis","estaríamos","estarían","estarías","estas","este","esto","estos","estoy","fui","fuimos","fueron","fui","ha","habida","habidas","habido","habidos","habiendo","habrá","habrán","había","habíamos","han","has","hasta","hay","haya","hayamos","hayan","hayas","hayáis","he","hemos","hube","hubo","la","las","le","les","lo","los","más","mas","me","mi","mis","mucho","muchos","muy","nada","ni","no","nos","nosotras","nosotros","nuestra","nuestras","nuestro","nuestros","o","os","otra","otras","otro","otros","para","pero","poco","por","porque","que","quien","quienes","se","sea","seamos","sean","seas","ser","seré","si","sido","siendo","sin","sobre","sois","somos","son","soy","su","sus","suya","suyas","suyo","suyos","también","tanto","te","tendrá","tendrán","tendrás","tendré","tendríamos","tendrían","tendrías","tened","teneis","tenemos","tenga","tengamos","tengan","tengas","tengo","tenida","tenidas","tenido","tenidos","teniendo","tenía","teníamos","ti","tiene","tienen","tienes","todo","todos","trabaja","trabajan","trabajar","trabajas","trabajo","trabajos","tu","tus","tuya","tuyas","tuyo","tuyos","un","una","uno","unos","vosotras","vosotros","vuestra","vuestras","vuestro","vuestros","y","ya","yo",
  ]);

  function extractTerms(text) {
    const map = new Map();
    const re = /[\p{L}][\p{L}\p{N}+#.-]{1,}/gu;
    const lower = text.toLowerCase();
    let m;
    while ((m = re.exec(lower)) !== null) {
      const t = m[0].replace(/[.,;:()\[\]"'`]/g, "");
      if (t.length < 3) continue;
      if (STOPWORDS.has(t)) continue;
      if (/^\d+$/.test(t)) continue;
      map.set(t, (map.get(t) || 0) + 1);
    }
    return [...map.entries()].sort((a, b) => b[1] - a[1]).map(([term, count]) => ({ term, count }));
  }

  function cvPlainText(data) {
    const parts = [];
    if (data.meta) {
      parts.push(data.meta.titulo_profesional || "");
      parts.push(data.meta.objetivo_cv || "");
    }
    if (data.perfil_profesional) parts.push(data.perfil_profesional.resumen || "");
    for (const e of data.experiencia || []) {
      parts.push(e.cargo || ""); parts.push(e.empresa || "");
      for (const r of e.responsabilidades || []) parts.push(r);
      for (const l of e.logros || []) parts.push(l);
    }
    for (const e of data.educacion || []) { parts.push(e.titulo || ""); parts.push(e.institucion || ""); }
    for (const h of [].concat(data.habilidades?.tecnicas || [], data.habilidades?.blandas || [], data.habilidades?.idiomas || [])) parts.push(h);
    for (const p of data.proyectos || []) {
      parts.push(p.nombre || ""); parts.push(p.descripcion || "");
      for (const t of p.tecnologias || []) parts.push(t);
    }
    return parts.join(" ");
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = jobText.value.trim();
    if (!text) { Shared.flash("Pegá el texto de la oferta.", "info"); return; }
    Storage.set(key, text);

    const data = CvStore.parseContext(cv);
    const jobTerms = extractTerms(text);
    const cvText = cvPlainText(data).toLowerCase();
    const cvSet = new Set(extractTerms(cvText).map((t) => t.term));

    const jobSet = new Set(jobTerms.map((t) => t.term));
    const hit = jobTerms.filter((t) => cvSet.has(t.term));
    const miss = jobTerms.filter((t) => !cvSet.has(t.term));

    const score = jobSet.size === 0 ? 0 : Math.round((hit.length / jobSet.size) * 100);
    scoreEl.textContent = `${score}% de coincidencia (${hit.length} de ${jobSet.size} términos)`;
    scoreEl.style.color = score >= 70 ? "var(--color-soft-indigo)" : score >= 40 ? "#d4a017" : "var(--danger-fg)";

    jobTermsEl.innerHTML = jobTerms.slice(0, 30).map((t) => `<li>${Shared.escapeHtml(t.term)} <span class="meta-muted">×${t.count}</span></li>`).join("") || "<li class=\"meta-muted\">(no se detectaron términos)</li>";
    cvTermsEl.innerHTML = hit.slice(0, 30).map((t) => `<li>${Shared.escapeHtml(t.term)}</li>`).join("") || "<li class=\"meta-muted\">(ninguno)</li>";
    missTermsEl.innerHTML = miss.slice(0, 30).map((t) => `<li>${Shared.escapeHtml(t.term)}</li>`).join("") || "<li class=\"meta-muted\">(ninguno)</li>";

    results.classList.remove("hidden");
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  });
})();
