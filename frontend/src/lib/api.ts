import axios from "axios";
import { supabase } from "./supabase";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000" });

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const fetchMe = (accessToken?: string) =>
  api.get<{ user_id: string; email: string; roles: { role: string; agency_id: string | null; brand_id: string | null }[] }>(
    "/tenants/me",
    accessToken ? { headers: { Authorization: `Bearer ${accessToken}` } } : undefined
  ).then(r => r.data);

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
  let resp;
  try {
    resp = await api.get(`/dashboard/export/${brandId}`, {
      params: filtered,
      responseType: "blob",
    });
  } catch (err: unknown) {
    // Try to extract the real error message from the blob response
    if (err && typeof err === "object" && "response" in err) {
      const axiosErr = err as { response?: { status: number; data?: Blob } };
      if (axiosErr.response?.data instanceof Blob) {
        try {
          const text = await axiosErr.response.data.text();
          const json = JSON.parse(text);
          throw new Error(`${axiosErr.response.status}: ${json.detail ?? text}`);
        } catch (parseErr) {
          if (parseErr instanceof Error && parseErr.message.startsWith(String(axiosErr.response.status))) throw parseErr;
        }
      }
      if (axiosErr.response?.status) throw new Error(`HTTP ${axiosErr.response.status}`);
    }
    throw err;
  }
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

export const createBrand = (payload: {
  name: string;
  keywords: string[];
  languages: string[];
  youtube_enabled?: boolean;
  youtube_channel_ids?: string[];
}) => api.post<{ id: string; name: string }>("/tenants/brands", payload).then(r => r.data);

export const updateBrandConfig = (brandId: string, payload: {
  youtube_enabled?: boolean;
  youtube_channel_ids?: string[];
  keywords?: string[];
  languages?: string[];
}) => api.put(`/tenants/brands/${brandId}/config`, payload).then(r => r.data);

export const deleteBrand = (brandId: string) =>
  api.delete(`/tenants/brands/${brandId}`).then(r => r.data);

export const deleteUserRole = (roleId: string) =>
  api.delete(`/tenants/users/roles/${roleId}`).then(r => r.data);

export const inviteUser = (payload: { email: string; role: string; brand_id?: string }) =>
  api.post<{ status: string; email: string }>("/tenants/users/invite", payload).then(r => r.data);

export const fetchBrandUsers = (brandId: string) =>
  api.get<import("./types").BrandUser[]>(`/tenants/users/${brandId}`).then(r => r.data);

// ── Phase 3 ────────────────────────────────────────────────────────────────────

export const fetchSentimentTrend = (
  brandId: string,
  params?: { days?: number; date_from?: string; date_to?: string }
) =>
  api
    .get<import("./types").SentimentTrendData>(`/dashboard/trends/${brandId}/sentiment`, { params })
    .then(r => r.data);

export const fetchSourceCategories = (
  brandId: string,
  params?: { date_from?: string; date_to?: string }
) =>
  api
    .get<import("./types").SourceCategoriesData>(`/dashboard/source-categories/${brandId}`, { params })
    .then(r => r.data);

export const fetchHeadlines = (
  brandId: string,
  tab: "positive" | "negative" | "trending",
  params?: { limit?: number; date_from?: string; date_to?: string }
) =>
  api
    .get<import("./types").HeadlinesData>(`/dashboard/headlines/${brandId}`, { params: { tab, ...params } })
    .then(r => r.data);

export const fetchReviewSummary = (
  brandId: string,
  params?: { date_from?: string; date_to?: string }
) =>
  api
    .get<import("./types").ReviewSummaryData>(`/dashboard/review-summary/${brandId}`, { params })
    .then(r => r.data);

export const fetchCompetitorSoV = (
  brandId: string,
  params?: { date_from?: string; date_to?: string }
) =>
  api
    .get<import("./types").CompetitorSoVData>(`/dashboard/competitor-sov/${brandId}`, { params })
    .then(r => r.data);

export const discoverCompetitors = (brandId: string) =>
  api
    .post<{ competitors: string[]; saved: boolean }>(
      `/dashboard/competitor-sov/${brandId}/discover`
    )
    .then(r => r.data);

export const fetchIssueClusters = (brandId: string, days = 30) =>
  api
    .get<import("./types").IssueClustersData>(`/dashboard/issue-clusters/${brandId}`, { params: { days } })
    .then(r => r.data);

export const fetchJournalistCoverage = (brandId: string, days = 90) =>
  api
    .get<import("./types").JournalistCoverageData>(`/dashboard/journalist-coverage/${brandId}`, { params: { days } })
    .then(r => r.data);

export const fetchToneBreakdown = (brandId: string, days = 30) =>
  api
    .get<import("./types").ToneBreakdownData>(`/dashboard/tone-breakdown/${brandId}`, { params: { days } })
    .then(r => r.data);

export const fetchDivergenceSummary = (brandId: string, days = 14) =>
  api
    .get<import("./types").DivergenceSummaryData>(`/dashboard/divergence-summary/${brandId}`, { params: { days } })
    .then(r => r.data);

export default api;
