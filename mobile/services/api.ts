import axios from "axios";
import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "mei_auth_token";

export const api = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000",
  timeout: 10000,
});

api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
    }
    return Promise.reject(error);
  }
);

export const salvarToken = (token: string) =>
  SecureStore.setItemAsync(TOKEN_KEY, token);

export const removerToken = () =>
  SecureStore.deleteItemAsync(TOKEN_KEY);

export const obterToken = () =>
  SecureStore.getItemAsync(TOKEN_KEY);
