// Renderiza el paso actual del asistente y guarda los datos en el CV.

(function () {
  const id = Shared.getCvId();
  if (!id) { Shared.flash("Falta el id del CV.", "error"); return; }
  const cv = CvStore.get(id);
  if (!cv) { Shared.flash("No se encontró el CV en este navegador.", "error"); return; }

  document.getElementById("back-link").href = `/cvs/${encodeURIComponent(id)}/edit`;
  document.getElementById("bc-edit").href = `/cvs/${encodeURIComponent(id)}/edit`;
  document.title = `Asistente · ${cv.title || "CV"}`;

  const stepParam = Shared.getQueryParam("step") || InterviewFlow.first().id;
  const step = InterviewFlow.get(stepParam);
  if (!step) {
    Shared.flash("Paso no encontrado.", "error");
    setTimeout(() => window.location.href = `/cvs/${encodeURIComponent(id)}/edit`, 1000);
    return;
  }

  const data = CvStore.parseContext(cv);
  const existing = step.load ? step.load(data) : {};
  const isRepeat = step.show_count && Array.isArray(_arrayFor(data, step.id)) && _arrayFor(data, step.id).length > 0;

  // Progress
  const allSteps = InterviewFlow.all();
  document.getElementById("step-num").textContent = String(InterviewFlow.indexOf(step.id) + 1);
  document.getElementById("step-total").textContent = String(allSteps.length);
  document.getElementById("step-title-name").textContent = step.title;

  // Title
  const stepTitle = document.getElementById("step-title");
  stepTitle.textContent = step.title;

  // Lede
  const ledeEl = document.getElementById("step-lede");
  if (step.lede) { ledeEl.textContent = step.lede; ledeEl.hidden = false; } else { ledeEl.hidden = true; }

  // Questions
  const qBlock = document.getElementById("questions-block");
  const qList = document.getElementById("questions-list");
  if (step.questions && step.questions.length) {
    qBlock.hidden = false;
    qList.innerHTML = step.questions.map((q) => `<p class="interview-question">${Shared.escapeHtml(q)}</p>`).join("");
  } else {
    qBlock.hidden = true;
  }

  // Back link
  const prev = InterviewFlow.prev(step.id);
  const backWrap = document.getElementById("back-step");
  if (prev) {
    backWrap.hidden = false;
    document.getElementById("back-step-link").href = `?id=${encodeURIComponent(id)}&step=${encodeURIComponent(prev.id)}`;
  } else {
    backWrap.hidden = true;
  }

  // Render fields
  const fieldsRoot = document.getElementById("fields-root");
  fieldsRoot.innerHTML = "";
  for (const f of step.fields) {
    const wrap = document.createElement("div");
    wrap.className = "field-group";
    const id = `f-${f.name}`;
    const labelEl = document.createElement("label");
    labelEl.setAttribute("for", id);
    labelEl.textContent = f.label;
    wrap.appendChild(labelEl);
    if (f.hint) {
      const h = document.createElement("p");
      h.className = "help";
      h.textContent = f.hint;
      wrap.appendChild(h);
    }
    let input;
    if (f.type === "textarea") {
      input = document.createElement("textarea");
      input.rows = 5;
      input.className = "code-area";
      input.value = existing[f.name] || "";
    } else if (f.type === "select") {
      input = document.createElement("select");
      input.className = "text-input";
      for (const opt of f.options || []) {
        const o = document.createElement("option");
        o.value = opt.value;
        o.textContent = opt.label;
        if ((existing[f.name] || "") === opt.value) o.selected = true;
        input.appendChild(o);
      }
    } else if (f.type === "checkbox") {
      input = document.createElement("input");
      input.type = "checkbox";
      input.value = "1";
      if (existing[f.name]) input.checked = true;
      input.id = id;
      const labelInline = document.createElement("label");
      labelInline.className = "checkbox-label";
      labelInline.appendChild(input);
      labelInline.appendChild(document.createTextNode(" " + f.label));
      wrap.innerHTML = "";
      wrap.appendChild(labelInline);
      fieldsRoot.appendChild(wrap);
      continue;
    } else {
      input = document.createElement("input");
      input.type = f.type;
      input.className = "text-input";
      input.id = id;
      input.name = f.name;
      input.value = existing[f.name] || "";
      if (f.autocomplete) input.setAttribute("autocomplete", f.autocomplete);
      if (f.placeholder) input.placeholder = f.placeholder;
      if (f.min != null) input.min = f.min;
      if (f.max != null) input.max = f.max;
    }
    input.id = id;
    input.name = f.name;
    wrap.appendChild(input);
    fieldsRoot.appendChild(wrap);
  }

  // Show count of existing items (for repeatable steps)
  if (step.show_count && isRepeat) {
    const arr = _arrayFor(data, step.id);
    const p = document.createElement("p");
    p.className = "help";
    p.textContent = `Ya tenés ${arr.length} entrada(s) en este bloque. Guardá esta para agregar otra.`;
    fieldsRoot.appendChild(p);
  }

  // Actions
  const actions = document.getElementById("form-actions");
  actions.innerHTML = "";
  const nextStep = InterviewFlow.next(step.id);
  const isLast = !nextStep;

  if (isLast) {
    const btn = document.createElement("button");
    btn.type = "submit";
    btn.name = "action";
    btn.value = "finish";
    btn.className = "btn btn-primary";
    btn.textContent = "Finalizar";
    actions.appendChild(btn);
  } else {
    const btn = document.createElement("button");
    btn.type = "submit";
    btn.name = "action";
    btn.value = "next";
    btn.className = "btn btn-primary";
    btn.textContent = step.show_count ? "Guardar y agregar otro" : "Guardar y continuar";
    actions.appendChild(btn);
    if (step.allow_skip) {
      const skip = document.createElement("button");
      skip.type = "submit";
      skip.name = "action";
      skip.value = "skip";
      skip.className = "btn btn-secondary";
      skip.textContent = "Saltar este paso";
      actions.appendChild(skip);
    }
  }

  // Form submit
  const form = document.getElementById("step-form");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const action = fd.get("action");

    if (action === "next" || action === "finish") {
      step.apply(data, fd);
    }
    // "skip" doesn't apply anything

    CvStore.saveContext(id, data);
    Shared.flash("Guardado en localStorage", "success");

    if (action === "finish" || !nextStep) {
      setTimeout(() => window.location.href = `/cvs/${encodeURIComponent(id)}/edit`, 400);
    } else {
      setTimeout(() => window.location.href = `/cvs/${encodeURIComponent(id)}/interview?step=${encodeURIComponent(nextStep.id)}`, 400);
    }
  });

  function _arrayFor(data, stepId) {
    if (stepId === "experiencia") return data.experiencia || [];
    if (stepId === "educacion") return data.educacion || [];
    if (stepId === "proyectos") return data.proyectos || [];
    if (stepId === "certificaciones") return data.certificaciones || [];
    return [];
  }
})();
