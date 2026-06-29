/** Componentes de form reusables para las secciones del editor. */

import { type ReactNode } from "react";

// ── Field wrapper ────────────────────────────────────────────────────────

interface FieldShellProps {
  label: string;
  htmlFor?: string;
  children: ReactNode;
  hint?: string;
}

export function FieldShell({ label, htmlFor, children, hint }: FieldShellProps) {
  return (
    <div className="form-field">
      <label htmlFor={htmlFor} className="form-field__label">
        {label}
      </label>
      {children}
      {hint && (
        <p className="form-field__hint" style={{ marginTop: 4 }}>
          {hint}
        </p>
      )}
    </div>
  );
}

// ── Inputs concretos ─────────────────────────────────────────────────────

interface TextFieldProps {
  label: string;
  htmlFor: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: "text" | "email" | "tel" | "url";
}

export function TextField({
  label,
  htmlFor,
  value,
  onChange,
  placeholder,
  type = "text",
}: TextFieldProps) {
  return (
    <FieldShell label={label} htmlFor={htmlFor}>
      <input
        id={htmlFor}
        type={type}
        className="text-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </FieldShell>
  );
}

interface TextAreaFieldProps {
  label: string;
  htmlFor: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  rows?: number;
}

export function TextAreaField({
  label,
  htmlFor,
  value,
  onChange,
  placeholder,
  rows = 3,
}: TextAreaFieldProps) {
  return (
    <FieldShell label={label} htmlFor={htmlFor}>
      <textarea
        id={htmlFor}
        className="text-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
      />
    </FieldShell>
  );
}

interface DateInputProps {
  label: string;
  htmlFor: string;
  value: string;
  onChange: (v: string) => void;
  hint?: string;
}

/** Input de fecha "YYYY-MM" para fechas de CV. */
export function DateInput({ label, htmlFor, value, onChange, hint }: DateInputProps) {
  return (
    <FieldShell label={label} htmlFor={htmlFor} hint={hint}>
      <input
        id={htmlFor}
        type="month"
        className="text-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </FieldShell>
  );
}

// ── Bullet list (líneas con add/remove, como en responsabilidades) ────────

interface BulletListProps {
  label: string;
  htmlFor?: string;
  values: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
}

/** TagInput: input de tags con Enter/coma/Backspace. Reusable. */
interface TagInputProps {
  label: string;
  values: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
}

export function TagInput({ label, values, onChange, placeholder }: TagInputProps) {
  const add = (raw: string) => {
    const v = raw.trim();
    if (!v) return;
    if (values.includes(v)) return;
    onChange([...values, v]);
  };

  const remove = (v: string) => onChange(values.filter((x) => x !== v));

  return (
    <div className="form-field">
      <label className="form-field__label">{label}</label>
      <div className="tag-input">
        {values.map((v) => (
          <span key={v} className="tag-chip">
            {v}
            <button
              type="button"
              className="tag-chip__x"
              onClick={() => remove(v)}
              aria-label={`Quitar ${v}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          className="tag-input__field"
          placeholder={placeholder}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === ",") {
              e.preventDefault();
              add(e.currentTarget.value);
              e.currentTarget.value = "";
            } else if (
              e.key === "Backspace" &&
              !e.currentTarget.value &&
              values.length > 0
            ) {
              remove(values[values.length - 1]);
            }
          }}
          onBlur={(e) => {
            if (e.currentTarget.value.trim()) {
              add(e.currentTarget.value);
              e.currentTarget.value = "";
            }
          }}
        />
      </div>
      <p className="help" style={{ marginTop: 4 }}>
        Enter o coma para agregar. Backspace para borrar el último.
      </p>
    </div>
  );
}

export function BulletList({
  label,
  htmlFor,
  values,
  onChange,
  placeholder,
}: BulletListProps) {
  const add = () => onChange([...values, ""]);
  const remove = (i: number) => onChange(values.filter((_, idx) => idx !== i));
  const update = (i: number, v: string) => {
    onChange(values.map((x, idx) => (idx === i ? v : x)));
  };

  return (
    <FieldShell label={label} htmlFor={htmlFor}>
      <ul className="bullet-list">
        {values.map((v, i) => (
          <li key={i} className="bullet-list__row">
            <textarea
              id={htmlFor ? `${htmlFor}-${i}` : undefined}
              className="text-input"
              rows={2}
              value={v}
              onChange={(e) => update(i, e.target.value)}
              placeholder={placeholder}
            />
            <button
              type="button"
              className="btn btn-ghost btn-compact"
              onClick={() => remove(i)}
              aria-label={`Quitar item ${i + 1}`}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
      <button
        type="button"
        className="btn btn-secondary btn-compact"
        onClick={add}
        style={{ marginTop: 4 }}
      >
        + Agregar item
      </button>
    </FieldShell>
  );
}
