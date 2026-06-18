// Cliente Supabase + tipos compartidos.
// Las credenciales vienen de Vite (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY).
import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error(
    "[supabase] Faltan VITE_SUPABASE_URL o VITE_SUPABASE_ANON_KEY. " +
      "Configuralas en .env.local o en Vercel → Environment Variables."
  );
}

export const supabase: SupabaseClient = createClient(
  supabaseUrl || "https://placeholder.supabase.co",
  supabaseAnonKey || "placeholder",
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  }
);

export type CV = {
  id: string;
  title: string;
  context_json: string;
  created_at: string;
  updated_at: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  patch?: Record<string, unknown> | null;
  created_at: string;
};
