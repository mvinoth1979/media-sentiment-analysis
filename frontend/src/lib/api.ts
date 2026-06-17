import axios from "axios";
import { supabase } from "./supabase";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000" });

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const fetchMe = () =>
  api.get<{ user_id: string; email: string; roles: { role: string; agency_id: string | null; brand_id: string | null }[] }>("/tenants/me")
     .then(r => r.data);

export const fetchBrands = (q = "") =>
  api.get<{ id: string; name: string; agency_id: string }[]>(`/tenants/brands?q=${encodeURIComponent(q)}`)
     .then(r => r.data);

export const fetchOverview = (brandId: string, days = 7) =>
  api.get<import("./types").OverviewData>(`/dashboard/overview/${brandId}?days=${days}`)
     .then(r => r.data);

export const fetchMentions = (brandId: string, params?: Record<string, string>) =>
  api.get(`/dashboard/mentions/${brandId}`, { params }).then(r => r.data);

export const fetchSources = (brandId: string) =>
  api.get<import("./types").SourceStat[]>(`/dashboard/sources/${brandId}`).then(r => r.data);

export const fetchTopics = (brandId: string) =>
  api.get<import("./types").TopicStat[]>(`/dashboard/topics/${brandId}`).then(r => r.data);

export const fetchAnnotations = (brandId: string) =>
  api.get<import("./types").Annotation[]>(`/dashboard/trends/${brandId}/annotations`).then(r => r.data);

export const createAnnotation = (brandId: string, date: string, label: string) =>
  api.post<import("./types").Annotation>(`/dashboard/trends/${brandId}/annotations`, { date, label })
     .then(r => r.data);

export const deleteMentions = (brandId: string, ids: string[]) =>
  api.delete<{ deleted: number }>(`/dashboard/mentions/${brandId}`, { data: { ids } })
     .then(r => r.data);

export const exportMentionsCsv = async (brandId: string, brandName: string, params: Record<string, string>) => {
  const filtered = Object.fromEntries(Object.entries(params).filter(([, v]) => v));
  const resp = await api.get(`/dashboard/export/${brandId}`, {
    params: filtered,
    responseType: "blob",
  });
  const url = URL.createObjectURL(new Blob([resp.data], { type: "text/csv" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = `mediasense-${brandName.replace(/\s+/g, "-").toLowerCase()}-${new Date().toISOString().split("T")[0]}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

export const fetchAlerts = (brandId: string) =>
  api.get<import("./types").AlertConfig[]>(`/dashboard/alerts/${brandId}`).then(r => r.data);

export const createAlert = (brandId: string, payload: { alert_type: string; threshold: number; notify_email: string }) =>
  api.post<import("./types").AlertConfig>(`/dashboard/alerts/${brandId}`, payload).then(r => r.data);

export const deleteAlert = (brandId: string, alertId: string) =>
  api.delete(`/dashboard/alerts/${brandId}/${alertId}`).then(r => r.data);

export const createBrand = (payload: { name: string; keywords: string[]; languages: string[] }) =>
  api.post<{ id: string; name: string }>("/tenants/brands", payload).then(r => r.data);

export const inviteUser = (payload: { email: string; role: string; brand_id?: string }) =>
  api.post<{ status: string; email: string }>("/tenants/users/invite", payload).then(r => r.data);

export const fetchBrandUsers = (brandId: string) =>
  api.get<import("./types").BrandUser[]>(`/tenants/users/${brandId}`).then(r => r.data);

export default api;
