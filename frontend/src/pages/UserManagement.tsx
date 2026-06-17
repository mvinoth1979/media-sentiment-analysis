import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchBrandUsers, inviteUser, deleteUserRole } from "../lib/api";
import type { BrandUser } from "../lib/types";

interface Props {
  brandId: string;
  brandName: string;
}

const ROLE_OPTIONS = [
  { value: "brand_admin",  label: "Brand Admin",   desc: "Full access for this brand" },
  { value: "brand_viewer", label: "Brand Viewer",  desc: "Read-only access" },
  { value: "agency_analyst", label: "Agency Analyst", desc: "Read across all agency brands" },
];

const ROLE_COLORS: Record<string, string> = {
  master_admin:   "bg-purple-900/40 text-purple-300 border-purple-700/50",
  agency_admin:   "bg-indigo-900/40 text-indigo-300 border-indigo-700/50",
  agency_analyst: "bg-blue-900/40 text-blue-300 border-blue-700/50",
  brand_admin:    "bg-teal-900/40 text-teal-300 border-teal-700/50",
  brand_viewer:   "bg-gray-700/60 text-gray-400 border-gray-600/50",
};

function RoleBadge({ role }: { role: string }) {
  const cls = ROLE_COLORS[role] ?? "bg-gray-700/60 text-gray-400 border-gray-600/50";
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${cls}`}>
      {role.replace(/_/g, " ")}
    </span>
  );
}

export function UserManagement({ brandId, brandName }: Props) {
  const [email, setEmail]   = useState("");
  const [role, setRole]     = useState("brand_viewer");
  const [invError, setInvError]     = useState("");
  const [invSuccess, setInvSuccess] = useState("");
  const [confirmRemove, setConfirmRemove] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const { data: users = [], isLoading } = useQuery<BrandUser[]>({
    queryKey: ["users", brandId],
    queryFn: () => fetchBrandUsers(brandId),
    staleTime: 30_000,
  });

  const removeMutation = useMutation({
    mutationFn: (roleId: string) => deleteUserRole(roleId),
    onSuccess: () => {
      setConfirmRemove(null);
      queryClient.invalidateQueries({ queryKey: ["users", brandId] });
    },
  });

  const inviteMutation = useMutation({
    mutationFn: () => inviteUser({ email: email.trim(), role, brand_id: brandId }),
    onSuccess: () => {
      setInvSuccess(`Invite sent to ${email} — they'll receive a magic-link email.`);
      setEmail("");
      setInvError("");
      queryClient.invalidateQueries({ queryKey: ["users", brandId] });
    },
    onError: (e: Error) => {
      setInvError(e.message);
      setInvSuccess("");
    },
  });

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-gray-100">Users — {brandName}</h2>
        <p className="text-xs text-gray-500 mt-0.5">Invite team members and manage their access level.</p>
      </div>

      {/* User list */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
          <span className="text-sm font-semibold text-gray-200">Team Members</span>
          <span className="text-xs text-gray-500">{users.length} user{users.length !== 1 ? "s" : ""}</span>
        </div>
        {isLoading ? (
          <div className="px-4 py-6 text-sm text-gray-500">Loading...</div>
        ) : users.length === 0 ? (
          <div className="px-4 py-6 text-sm text-gray-500 text-center">
            No users with direct brand access yet.<br />
            <span className="text-xs text-gray-600">Agency-level users have access via their agency role.</span>
          </div>
        ) : (
          <div className="divide-y divide-gray-800">
            {users.map((u: BrandUser) => (
              <div key={u.id} className="px-4 py-3 flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-gray-200 truncate">
                    {u.email || <span className="text-gray-600 italic">email not available</span>}
                  </div>
                  <div className="text-xs text-gray-600 mt-0.5 font-mono">{u.user_id.slice(0, 8)}…</div>
                </div>
                <RoleBadge role={u.role} />
                {confirmRemove === u.id ? (
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-red-400">Remove access?</span>
                    <button
                      onClick={() => removeMutation.mutate(u.id)}
                      disabled={removeMutation.isPending}
                      className="text-xs px-2 py-0.5 bg-red-700 hover:bg-red-600 text-white rounded disabled:opacity-50"
                    >
                      {removeMutation.isPending ? "…" : "Remove"}
                    </button>
                    <button onClick={() => setConfirmRemove(null)} className="text-xs text-gray-500 hover:text-gray-300">
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setConfirmRemove(u.id)}
                    className="shrink-0 text-gray-600 hover:text-red-400 transition-colors"
                    title="Remove user access"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Invite form */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
        <div className="text-sm font-semibold text-gray-200">Invite New User</div>
        <p className="text-xs text-gray-500 -mt-2">
          A magic-link email is sent automatically via Supabase — no password needed.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="text-xs text-gray-400">Email address</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="user@company.com"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-100 px-3 py-2 focus:outline-none focus:border-indigo-500 placeholder:text-gray-600"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs text-gray-400">Role</label>
            <select
              value={role}
              onChange={e => setRole(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-100 px-3 py-2 focus:outline-none focus:border-indigo-500"
            >
              {ROLE_OPTIONS.map(r => (
                <option key={r.value} value={r.value}>{r.label} — {r.desc}</option>
              ))}
            </select>
          </div>
        </div>

        {invError && <p className="text-xs text-red-400">{invError}</p>}
        {invSuccess && <p className="text-xs text-emerald-400">{invSuccess}</p>}

        <button
          onClick={() => inviteMutation.mutate()}
          disabled={!email.trim() || inviteMutation.isPending}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg disabled:opacity-40 transition-colors"
        >
          {inviteMutation.isPending ? "Sending invite…" : "Send Invite"}
        </button>
      </div>
    </div>
  );
}
