// Sync entre localStorage (primario) y la API de Flask (secundario).
// Estrategia:
//   1. localStorage es la fuente de verdad local (offline-first)
//   2. Sync empuja los locales que el server no tiene
//   3. Sync trae los remotos que localStorage no tiene
//   4. En conflicto (mismo id, distinto updated_at), gana el más reciente

const CvSync = (() => {
  // El id local es tipo "lena-2026-…" (timestamp+random).
  // El id del server es int. Para evitar colisiones, el server genera
  // su propio id y el local mantiene el suyo. Sync empuja por título + updated_at.

  async function pushLocal(localCvs) {
    let pushed = 0, failed = 0;
    for (const local of localCvs) {
      try {
        // Si el local tiene un serverId (creado tras un sync previo), update
        if (local.serverId) {
          await ApiClient.updateCv(local.serverId, {
            title: local.title,
            context_json: local.context_json,
          });
        } else {
          // Crear nuevo en el server
          const remote = await ApiClient.createCv({
            title: local.title,
            context_json: local.context_json,
          });
          // Guardar el serverId en el local para futuros updates
          const updated = CvStore.update(local.id, { serverId: remote.id });
          if (updated) {
            // Mapear serverId en una clave separada para no romper nada
            try {
              localStorage.setItem("creator_cv:server_id:" + local.id, String(remote.id));
            } catch {}
          }
        }
        pushed++;
      } catch (e) {
        console.warn("push failed for", local.title, e.message);
        failed++;
      }
    }
    return { pushed, failed };
  }

  async function pullRemote() {
    const remote = await ApiClient.listCvs();
    const local = CvStore.list();
    let pulled = 0, conflicts = 0;
    for (const r of remote) {
      // Buscar un local que tenga este serverId
      const match = local.find((l) => l.serverId === r.id);
      if (match) {
        // Comparar updated_at: gana el más reciente
        if (new Date(r.updated_at) > new Date(match.updated_at)) {
          CvStore.update(match.id, {
            title: r.title,
            context_json: r.context_json,
            updated_at: r.updated_at,
          });
          pulled++;
        } else if (new Date(r.updated_at) < new Date(match.updated_at)) {
          // Local más nuevo: empujar al server
          try {
            await ApiClient.updateCv(r.id, {
              title: match.title,
              context_json: match.context_json,
            });
            pulled++;
          } catch (e) {
            conflicts++;
          }
        } else {
          // Iguales: nada que hacer
        }
      } else {
        // No hay local con este serverId: importar
        // Pero evitar duplicar por título
        const dupByTitle = local.find((l) => l.title === r.title);
        if (dupByTitle) {
          // Mapear: el local ya tiene este título, solo guardar el serverId
          try {
            localStorage.setItem("creator_cv:server_id:" + dupByTitle.id, String(r.id));
            CvStore.update(dupByTitle.id, { serverId: r.id });
          } catch {}
        } else {
          // Crear local con el serverId
          const localId = CvStore.create({
            title: r.title,
            context_json: r.context_json,
          }).id;
          try {
            localStorage.setItem("creator_cv:server_id:" + localId, String(r.id));
            CvStore.update(localId, { serverId: r.id, updated_at: r.updated_at });
          } catch {}
          pulled++;
        }
      }
    }
    return { pulled, conflicts };
  }

  // Migrar los serverIds desde localStorage al CvStore
  function loadServerIds() {
    const cvs = CvStore.list();
    for (const cv of cvs) {
      try {
        const sid = localStorage.getItem("creator_cv:server_id:" + cv.id);
        if (sid && !cv.serverId) {
          CvStore.update(cv.id, { serverId: parseInt(sid, 10) });
        }
      } catch {}
    }
  }

  async function syncAll() {
    const start = Date.now();
    if (!(await ApiClient.health())) {
      throw new Error("API no disponible. ¿Hay backend configurado?");
    }
    loadServerIds();
    const local = CvStore.list();
    const pushResult = await pushLocal(local);
    const pullResult = await pullRemote();
    return {
      duration_ms: Date.now() - start,
      pushed: pushResult.pushed,
      push_failed: pushResult.failed,
      pulled: pullResult.pulled,
      conflicts: pullResult.conflicts,
    };
  }

  return { syncAll, pushLocal, pullRemote };
})();

window.CvSync = CvSync;
