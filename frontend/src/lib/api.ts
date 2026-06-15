import axios from "axios";
import { supabase } from "./supabase";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000" });

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const fetchOverview = (brandId: string, days = 7) =>
  api.get<import("./types").OverviewData>(`/dashboard/overview/${brandId}?days=${days}`)
     .then(r => r.data);

export const fetchMentions = (brandId: string, params?: Record<string, string>) =>
  api.get(`/dashboard/mentions/${brandId}`, { params }).then(r => r.data);

export default api;
