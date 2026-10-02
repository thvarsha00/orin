import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, getToken, setToken } from "../services/api";
import type { Profile, User } from "../types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string, lang: string) => Promise<void>;
  logout: () => void;
  updateProfile: (p: Partial<Profile>) => Promise<void>;
}

const Ctx = createContext<AuthState | null>(null);
export const useAuth = () => {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth outside AuthProvider");
  return v;
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(!!getToken());

  useEffect(() => {
    if (!getToken()) return;
    api<User>("/auth/me").then(setUser).catch(() => setToken(null)).finally(() => setLoading(false));
  }, []);

  const finish = (r: { access_token: string; user: User }) => { setToken(r.access_token); setUser(r.user); };

  const login = useCallback(async (email: string, password: string) =>
    finish(await api("/auth/login", "POST", { email, password })), []);
  const register = useCallback(async (email: string, password: string, display_name: string, preferred_language: string) =>
    finish(await api("/auth/register", "POST", { email, password, display_name, preferred_language })), []);
  const logout = useCallback(() => { setToken(null); setUser(null); }, []);
  const updateProfile = useCallback(async (p: Partial<Profile>) =>
    setUser(await api<User>("/auth/me/profile", "PATCH", p)), []);

  return <Ctx.Provider value={{ user, loading, login, register, logout, updateProfile }}>{children}</Ctx.Provider>;
}
