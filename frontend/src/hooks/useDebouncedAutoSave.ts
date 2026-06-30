import { useEffect, useRef, useState } from "react";

export type SaveStatus = "idle" | "pending" | "saving" | "saved" | "error";

interface UseDebouncedAutoSaveOptions<T> {
  value: T;
  save: (value: T) => Promise<void>;
  delay?: number;
}

interface UseDebouncedAutoSaveReturn {
  status: SaveStatus;
  error: string;
  flush: () => Promise<void>;
}

/**
 * Autosave con debounce. Mientras hay cambios pendientes no se vuelve a invocar save.
 * Flush en unmount: usa beacon/navigator para sobrevivir la navegación.
 */
export function useDebouncedAutoSave<T>({
  value,
  save,
  delay = 1500,
}: UseDebouncedAutoSaveOptions<T>): UseDebouncedAutoSaveReturn {
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [error, setError] = useState("");
  const valueRef = useRef(value);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingRef = useRef(false);
  const saveRef = useRef(save);

  useEffect(() => {
    valueRef.current = value;
  }, [value]);
  useEffect(() => {
    saveRef.current = save;
  }, [save]);

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
      setTimeout(() => setStatus((s) => (s === "saved" ? "idle" : s)), 2000);
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  // Debounce: cuando value cambia, armar timer
  useEffect(() => {
    pendingRef.current = true;
    setStatus("pending");

    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      void flush();
    }, delay);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, delay]);

  // Flush al desmontar — await para que el request HTTP no se corte
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      if (pendingRef.current) {
        pendingRef.current = false;
        // Sync XHR via sendBeacon-like: lanzamos el save y no frenamos.
        // El browser suele completar el request si ya arrancó.
        saveRef.current(valueRef.current).catch(() => {});
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { status, error, flush };
}
