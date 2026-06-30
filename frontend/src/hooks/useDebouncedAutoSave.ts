import { useEffect, useRef, useState } from "react";

export type SaveStatus = "idle" | "pending" | "saving" | "saved" | "error";

interface UseDebouncedAutoSaveOptions<T> {
  value: T;
  save: (value: T) => Promise<void>;
  /** Key for localStorage backup. When provided, pending data is backed up locally. */
  storageKey?: string;
  delay?: number;
}

interface UseDebouncedAutoSaveReturn<T> {
  status: SaveStatus;
  error: string;
  flush: () => Promise<void>;
  /** If localStorage had a backup on mount, this is the restored value. null otherwise. */
  restoredFromStorage: T | null;
}

/**
 * Autosave con debounce + backup en localStorage.
 *
 * - Cada cambio escribe a localStorage inmediatamente.
 * - Debounced save al backend.
 * - En unmount, intenta fetch con keepalive: true (sobrevive F5/close).
 * - En mount, si localStorage tiene datos, los devuelve como `restoredFromStorage`
 *   para que el componente los use en su estado inicial.
 */
export function useDebouncedAutoSave<T>({
  value,
  save,
  storageKey,
  delay = 800,
}: UseDebouncedAutoSaveOptions<T>): UseDebouncedAutoSaveReturn<T> {
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [error, setError] = useState("");
  const valueRef = useRef(value);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingRef = useRef(false);
  const saveRef = useRef(save);
  const [restoredFromStorage, setRestoredFromStorage] = useState<T | null>(null);

  useEffect(() => {
    valueRef.current = value;
  }, [value]);
  useEffect(() => {
    saveRef.current = save;
  }, [save]);

  // ── localStorage helpers ─────────────────────────────────────────────

  const writeToStorage = (val: T) => {
    if (!storageKey) return;
    try {
      localStorage.setItem(storageKey, JSON.stringify(val));
    } catch { /* quota or private mode */ }
  };

  const readFromStorage = (): T | null => {
    if (!storageKey) return null;
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return null;
      return JSON.parse(raw) as T;
    } catch { return null; }
  };

  const clearStorage = () => {
    if (!storageKey) return;
    try { localStorage.removeItem(storageKey); } catch { /* */ }
  };

  // En mount: si hay backup en localStorage, devolverlo
  useEffect(() => {
    const backup = readFromStorage();
    if (backup !== null) {
      setRestoredFromStorage(backup);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const flush = async () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (!pendingRef.current && status !== "error") return;
    pendingRef.current = false;
    setStatus("saving");
    try {
      await saveRef.current(valueRef.current);
      setStatus("saved");
      setError("");
      clearStorage();
      setTimeout(() => setStatus((s) => (s === "saved" ? "idle" : s)), 2000);
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  // Debounce: cuando value cambia, armar timer + backup a localStorage
  useEffect(() => {
    pendingRef.current = true;
    setStatus("pending");
    writeToStorage(value);

    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      void flush();
    }, delay);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, delay]);

  // Flush al desmontar — keepalive fetch sobrevive F5 / cierre de tab
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      if (pendingRef.current) {
        pendingRef.current = false;
        // Backup inmediato a localStorage
        writeToStorage(valueRef.current);
        // Intentar save final con keepalive
        const match = window.location.pathname.match(/\/cv\/([^/]+)/);
        if (match) {
          const token = localStorage.getItem("access_token");
          const contextStr = JSON.stringify(valueRef.current, null, 2);
          const body = JSON.stringify({ context_json: contextStr });
          const blob = new Blob([body], { type: "application/json" });
          try {
            fetch(`/api/cvs/${match[1]}`, {
              method: "PUT",
              headers: {
                "Content-Type": "application/json",
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
              },
              body: blob,
              keepalive: true,
            }).then((res) => {
              if (res.ok) clearStorage();
            }).catch(() => { /* localStorage backup remains */ });
          } catch { /* localStorage backup remains */ }
        }
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { status, error, flush, restoredFromStorage };
}
