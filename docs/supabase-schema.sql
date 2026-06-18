-- Schema para Supabase (Postgres).
-- Corré esto en Supabase → SQL Editor → New query → pega y ejecutá.
-- Debe coincidir con creator_cv/models.py

-- ── users ────────────────────────────────────────────────────────
-- Un solo usuario por ahora (single-user, dev@local).
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO users (email) VALUES ('dev@local')
ON CONFLICT (email) DO NOTHING;

-- ── cvs ──────────────────────────────────────────────────────────
-- El context_json se guarda como TEXT (JSON en string).
-- review_markdown y chat_history_json son columnas adicionales en la misma tabla.
CREATE TABLE IF NOT EXISTS cvs (
    id                  SERIAL PRIMARY KEY,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title               VARCHAR(255) NOT NULL DEFAULT '',
    context_json        TEXT NOT NULL DEFAULT '{}',
    review_markdown     TEXT,
    chat_history_json   TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cvs_user_id ON cvs(user_id);
CREATE INDEX IF NOT EXISTS idx_cvs_updated_at ON cvs(updated_at DESC);

-- Trigger para actualizar updated_at automáticamente en UPDATE
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_cvs_updated_at ON cvs;
CREATE TRIGGER update_cvs_updated_at
BEFORE UPDATE ON cvs
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ── cv_sections (reservado para futuro; el chat ya está en cvs.chat_history_json) ─
CREATE TABLE IF NOT EXISTS cv_sections (
    id          SERIAL PRIMARY KEY,
    cv_id       INTEGER NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    key         VARCHAR(64) NOT NULL,
    body        TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(cv_id, key)
);

CREATE INDEX IF NOT EXISTS idx_cv_sections_cv_id ON cv_sections(cv_id);

-- ── Verificar ───────────────────────────────────────────────────
SELECT 'users' AS tabla, COUNT(*) AS filas FROM users
UNION ALL
SELECT 'cvs', COUNT(*) FROM cvs
UNION ALL
SELECT 'cv_sections', COUNT(*) FROM cv_sections;
