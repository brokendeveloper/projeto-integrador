import React, { createContext, useContext, useState, useEffect } from "react";
import { api, salvarToken, removerToken, obterToken } from "../services/api";

interface AuthContextData {
  autenticado: boolean | null;
  login: (email: string, senha: string) => Promise<void>;
  registrar: (nome: string, email: string, cnpj: string, senha: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextData | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [autenticado, setAutenticado] = useState<boolean | null>(null);

  // Verifica token salvo ao iniciar o app
  useEffect(() => {
    obterToken().then((token) => setAutenticado(!!token));
  }, []);

  // Intercepta 401 globalmente: limpa token e redireciona para login
  useEffect(() => {
    const interceptorId = api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          await removerToken();
          setAutenticado(false);
        }
        return Promise.reject(error);
      }
    );
    return () => api.interceptors.response.eject(interceptorId);
  }, []);

  async function login(email: string, senha: string) {
    const { data } = await api.post("/auth/login", { email, senha });
    await salvarToken(data.access_token);
    setAutenticado(true);
  }

  async function registrar(nome: string, email: string, cnpj: string, senha: string) {
    const { data } = await api.post("/auth/register", { nome, email, cnpj, senha });
    await salvarToken(data.access_token);
    setAutenticado(true);
  }

  async function logout() {
    await removerToken();
    setAutenticado(false);
  }

  return (
    <AuthContext.Provider value={{ autenticado, login, registrar, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider");
  }
  return context;
}
