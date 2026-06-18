// Importador de CVs desde JSON (formato export_to_json.py).
// Se puede llamar desde la consola del navegador en la página /:
//   import('./assets/js/import-cvs.js').then(m => m.importExport(...))

const CvImporter = (() => {
  function importFromExport(data) {
    if (!data || !Array.isArray(data.cvs)) throw new Error("Formato inválido");
    let count = 0;
    for (const item of data.cvs) {
      // Saltar si ya existe un CV con el mismo título
      const existing = CvStore.list().find((cv) => cv.title === item.title);
      if (existing) continue;
      const cv = CvStore.create({
        title: item.title || "Sin título",
        context_json: typeof item.context_json === "string"
          ? item.context_json
          : JSON.stringify(item.context || item.context_json || {}, null, 2),
      });
      count++;
    }
    return count;
  }

  function importFromFullBackup(data) {
    // Backup completo de localStorage (formato Storage.exportAll)
    Storage.importAll(data, { merge: false });
    return Object.keys(data).filter((k) => k.startsWith("cvs:") && k !== "cvs:index").length;
  }

  return { importFromExport, importFromFullBackup };
})();

window.CvImporter = CvImporter;
