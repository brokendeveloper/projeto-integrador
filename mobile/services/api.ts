import axios from "axios";
import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "mei_auth_token";

export const api = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000",
  timeout: 10000,
});

// Injeta o token JWT em todas as requisições
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// O tratamento de 401 fica no AuthContext para poder atualizar o estado de auth

export const salvarToken = (token: string) =>
  SecureStore.setItemAsync(TOKEN_KEY, token);

export const removerToken = () =>
  SecureStore.deleteItemAsync(TOKEN_KEY);

export const obterToken = () =>
  SecureStore.getItemAsync(TOKEN_KEY);
