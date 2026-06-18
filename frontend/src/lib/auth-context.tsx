import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { apiLogin, apiMe, apiRegister } from "./api";

type AuthState =
  | { status: "loading" }
  | { status: "authenticated"; userId: string; email: string }
  | { status: "unauthenticated" };

type AuthContextValue = AuthState & {
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "loading" });

  const checkSession = useCallback(async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setState({ status: "unauthenticated" });
      return;
    }
    try {
      const { user_id, email } = await apiMe();
      setState({ status: "authenticated", userId: user_id, email });
    } catch {
      localStorage.removeItem("token");
      localStorage.removeItem("user_id");
      localStorage.removeItem("email");
      setState({ status: "unauthenticated" });
    }
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  const signIn = async (email: string, password: string) => {
    const result = await apiLogin(email, password);
    localStorage.setItem("token", result.token);
    localStorage.setItem("user_id", result.user_id);
    localStorage.setItem("email", result.email);
    setState({ status: "authenticated", userId: result.user_id, email: result.email });
  };

  const signUp = async (email: string, password: string) => {
    const result = await apiRegister(email, password);
    localStorage.setItem("token", result.token);
    localStorage.setItem("user_id", result.user_id);
    localStorage.setItem("email", result.email);
    setState({ status: "authenticated", userId: result.user_id, email: result.email });
  };

  const signOut = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("email");
    setState({ status: "unauthenticated" });
  };

  return (
    <AuthContext.Provider value={{ ...state, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
