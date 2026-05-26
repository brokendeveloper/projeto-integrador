import { useState, useEffect } from "react";
import { api, salvarToken, removerToken, obterToken } from "../services/api";

export function useAuth() {
  const [autenticado, setAutenticado] = useState<boolean | null>(null);

  useEffect(() => {
    obterToken().then((token) => setAutenticado(!!token));
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

  return { autenticado, login, registrar, logout };
}
