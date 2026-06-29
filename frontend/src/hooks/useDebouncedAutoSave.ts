import { useEffect, useRef, useState } from "react";

export type SaveStatus = "idle" | "pending" | "saving" | "saved" | "error";

interface UseDebouncedAutoSaveOptions<T> {
  /** Valor actual a persistir. */
  value: T;
  /** Función async que persiste en backend. */
  save: (value: T) => Promise<void>;
  /** Debounce en ms. Default 1500. */
  delay?: number;
}

interface UseDebouncedAutoSaveReturn {
  status: SaveStatus;
  error: string;
  /** Llamar manualmente (e.g. antes de unmount). */
  flush: () => Promise<void>;
}

/**
 * Autosave con debounce. Mientras hay cambios pendientes no se vuelve a invocar ``save``.
 * Expone un estado derivable para el indicador "Guardando… / Guardado ✓".
 *
 * Política de "último gana": si el usuario sigue editando, el save más viejo se descarta.
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
  const inFlightRef = useRef<Promise<void> | null>(null);
  const saveRef = useRef(save);

  // Mantener refs actualizados (sin causar re-renders)
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
      // Volver a "idle" después de 2s para que "Guardado ✓" se vea
      setTimeout(() => setStatus((s) => (s === "saved" ? "idle" : s)), 2000);
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  // Cuando ``value`` cambia, armar un timer.
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

  // Flush al desmontar
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      // Si había cambios pendientes, intentamos guardar
      if (pendingRef.current) {
        void saveRef.current(valueRef.current).catch(() => {
          /* swallow en unmount */
        });
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { status, error, flush };
}
