-- Schema para Supabase (Postgres).
-- Corré esto en Supabase → SQL Editor → New query → pegá todo → Run.
--
-- Si el SQL Editor dice "policy already exists" en alguna parte,
-- agregá `DROP POLICY IF EXISTS <name> ON <table>;` antes de cada CREATE POLICY.

-- ── Tabla: cvs ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.cvs (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title         text NOT NULL DEFAULT 'Sin título',
    context_json  text NOT NULL DEFAULT '{}',
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cvs_user_id ON public.cvs(user_id);
CREATE INDEX IF NOT EXISTS idx_cvs_updated_at ON public.cvs(updated_at DESC);

-- Trigger: updated_at automático
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_cvs_updated_at ON public.cvs;
CREATE TRIGGER trg_cvs_updated_at
BEFORE UPDATE ON public.cvs
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

-- ── Tabla: chat_histories ────────────────────────────────────────
-- Un chat por CV. Mensajes guardados como JSONB array.
CREATE TABLE IF NOT EXISTS public.chat_histories (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cv_id       uuid NOT NULL UNIQUE REFERENCES public.cvs(id) ON DELETE CASCADE,
    user_id     uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    messages    jsonb NOT NULL DEFAULT '[]'::jsonb,
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_histories_cv_id ON public.chat_histories(cv_id);
CREATE INDEX IF NOT EXISTS idx_chat_histories_user_id ON public.chat_histories(user_id);

DROP TRIGGER IF EXISTS trg_chat_histories_updated_at ON public.chat_histories;
CREATE TRIGGER trg_chat_histories_updated_at
BEFORE UPDATE ON public.chat_histories
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

-- ── Row Level Security (RLS) ─────────────────────────────────────
-- Cada usuario solo ve/modifica sus propios CVs y chats.
ALTER TABLE public.cvs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_histories ENABLE ROW LEVEL SECURITY;

-- cvs: el usuario solo ve sus filas
DROP POLICY IF EXISTS "Users can view their own cvs" ON public.cvs;
CREATE POLICY "Users can view their own cvs" ON public.cvs
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own cvs" ON public.cvs;
CREATE POLICY "Users can insert their own cvs" ON public.cvs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own cvs" ON public.cvs;
CREATE POLICY "Users can update their own cvs" ON public.cvs
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own cvs" ON public.cvs;
CREATE POLICY "Users can delete their own cvs" ON public.cvs
    FOR DELETE USING (auth.uid() = user_id);

-- chat_histories: igual
DROP POLICY IF EXISTS "Users can view their own chat histories" ON public.chat_histories;
CREATE POLICY "Users can view their own chat histories" ON public.chat_histories
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own chat histories" ON public.chat_histories;
CREATE POLICY "Users can insert their own chat histories" ON public.chat_histories
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own chat histories" ON public.chat_histories;
CREATE POLICY "Users can update their own chat histories" ON public.chat_histories
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own chat histories" ON public.chat_histories;
CREATE POLICY "Users can delete their own chat histories" ON public.chat_histories
    FOR DELETE USING (auth.uid() = user_id);
