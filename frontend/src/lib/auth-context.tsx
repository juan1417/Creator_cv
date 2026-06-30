import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  apiLogin,
  apiLogout,
  apiMe,
  apiRegister,
  apiVerifyEmail,
  apiVerifyTwoFactor,
  type LoginOrPending,
  type LoginPendingResult,
  type LoginResult,
  type RegisterResult,
} from "./api";

type AuthState =
  | { status: "loading" }
  | { status: "authenticated"; userId: string; email: string }
  | { status: "unauthenticated" };

type AuthContextValue = AuthState & {
  signIn: (email: string, password: string) => Promise<LoginOrPending>;
  /**
   * Registra un usuario nuevo.
   *
   * Si el backend requiere verificación de email, devuelve un result SIN tokens.
   * Si requiere verificación de email Y 2FA → devuelve pending.
   * Si skip_verification (dev), abre sesión directamente.
   */
  signUp: (email: string, password: string) => Promise<RegisterResult>;
  verifyEmail: (token: string) => Promise<LoginOrPending>;
  verifyTwoFactor: (pendingToken: string, code: string) => Promise<LoginResult>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function isPending(r: LoginOrPending): r is LoginPendingResult {
  return (r as LoginPendingResult).requires_2fa === true;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "loading" });

  const handleSessionExpired = useCallback(() => {
    setState({ status: "unauthenticated" });
  }, []);

  const checkSession = useCallback(async () => {
    const access = localStorage.getItem("access_token");
    if (!access) {
      setState({ status: "unauthenticated" });
      return;
    }
    try {
      const { user_id, email } = await apiMe(handleSessionExpired);
      setState({ status: "authenticated", userId: user_id, email });
    } catch {
      setState({ status: "unauthenticated" });
    }
  }, [handleSessionExpired]);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  const signIn = async (email: string, password: string): Promise<LoginOrPending> => {
    const result = await apiLogin(email, password, handleSessionExpired);
    if (!isPending(result)) {
      setState({
        status: "authenticated",
        userId: result.user_id,
        email: result.email,
      });
    }
    return result;
  };

  const signUp = async (
    email: string,
    password: string
  ): Promise<RegisterResult> => {
    const result = await apiRegister(email, password);
    if (!result.requires_verification && result.access_token) {
      setState({
        status: "authenticated",
        userId: result.user_id,
        email: result.email,
      });
    }
    return result;
  };

  const verifyEmail = async (token: string): Promise<LoginOrPending> => {
    const result = await apiVerifyEmail(token);
    if (!isPending(result)) {
      setState({
        status: "authenticated",
        userId: result.user_id,
        email: result.email,
      });
    }
    return result;
  };

  const verifyTwoFactor = async (
    pendingToken: string,
    code: string
  ): Promise<LoginResult> => {
    const result = await apiVerifyTwoFactor(pendingToken, code);
    setState({
      status: "authenticated",
      userId: result.user_id,
      email: result.email,
    });
    return result;
  };

  const signOut = async () => {
    await apiLogout(handleSessionExpired);
    setState({ status: "unauthenticated" });
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        signIn,
        signUp,
        verifyEmail,
        verifyTwoFactor,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
