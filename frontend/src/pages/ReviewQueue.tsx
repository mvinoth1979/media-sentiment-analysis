import { useEffect, useState } from "react";
import api from "../lib/api";

interface ReviewQueueItem {
  id: string;
  brand_id: string;
  article_id: string;
  reason: string;
  status: "pending" | "approved" | "rejected";
  reviewer_id: string | null;
  reviewed_at: string | null;
  created_at: string | null;
  article_title: string | null;
  article_url: string | null;
}

interface ReviewQueueResponse {
  items: ReviewQueueItem[];
  total: number;
}

type StatusFilter = "pending" | "approved" | "rejected";

interface Props {
  brandId: string;
  brandName: string;
}

function timeAgo(iso: string | null): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "yesterday";
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "pending"
      ? "bg-amber-100 text-amber-700 border border-amber-200"
      : status === "approved"
      ? "bg-green-100 text-green-700 border border-green-200"
      : "bg-red-100 text-red-700 border border-red-200";
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold capitalize ${cls}`}>
      {status}
    </span>
  );
}

function ReasonBadge({ reason }: { reason: string }) {
  const isCrisis = reason.includes("crisis");
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium ${
        isCrisis
          ? "bg-red-50 text-red-600 border border-red-100"
          : "bg-blue-50 text-blue-600 border border-blue-100"
      }`}
    >
      {reason.replace(/_/g, " ")}
    </span>
  );
}

function QueueItemRow({
  item,
  onDecision,
}: {
  item: ReviewQueueItem;
  onDecision: (id: string, status: "approved" | "rejected") => Promise<void>;
}) {
  const [busy, setBusy] = useState<"approving" | "rejecting" | null>(null);

  const handleDecision = async (status: "approved" | "rejected") => {
    setBusy(status === "approved" ? "approving" : "rejecting");
    try {
      await onDecision(item.id, status);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="border border-gray-100 rounded-lg p-4 hover:bg-gray-50/50 transition-colors">
      <div className="flex items-start gap-3">
        {/* Left: article info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <StatusBadge status={item.status} />
            <ReasonBadge reason={item.reason} />
            <span className="text-[10px] text-gray-400">{timeAgo(item.created_at)}</span>
          </div>

          {item.article_title ? (
            <a
              href={item.article_url || "#"}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-gray-800 hover:text-blue-600 hover:underline line-clamp-2 leading-snug"
            >
              {item.article_title}
            </a>
          ) : (
            <div className="text-sm text-gray-400 italic">Article not found (id: {item.article_id})</div>
          )}

          {item.reviewed_at && (
            <div className="text-[10px] text-gray-400 mt-1">
              Reviewed {timeAgo(item.reviewed_at)}
            </div>
          )}
        </div>

        {/* Right: action buttons (only for pending) */}
        {item.status === "pending" && (
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => handleDecision("approved")}
              disabled={busy !== null}
              className="px-3 py-1.5 text-xs font-medium bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {busy === "approving" ? "..." : "Approve"}
            </button>
            <button
              onClick={() => handleDecision("rejected")}
              disabled={busy !== null}
              className="px-3 py-1.5 text-xs font-medium bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {busy === "rejecting" ? "..." : "Reject"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function SkeletonRow() {
  return (
    <div className="border border-gray-100 rounded-lg p-4 animate-pulse">
      <div className="flex items-start gap-3">
        <div className="flex-1 space-y-2">
          <div className="flex gap-2">
            <div className="h-4 w-16 bg-gray-200 rounded" />
            <div className="h-4 w-28 bg-gray-100 rounded" />
          </div>
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-3 bg-gray-100 rounded w-1/2" />
        </div>
        <div className="flex gap-2 shrink-0">
          <div className="h-7 w-16 bg-gray-200 rounded" />
          <div className="h-7 w-14 bg-gray-100 rounded" />
        </div>
      </div>
    </div>
  );
}

export function ReviewQueue({ brandId, brandName }: Props) {
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("pending");

  const fetchQueue = async (status: StatusFilter) => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { status };
      const resp = await api.get<ReviewQueueResponse>(
        `/dashboard/review-queue/${brandId}`,
        { params }
      );
      setItems(resp.data.items);
      setTotal(resp.data.total);
    } catch {
      setError("Failed to load review queue.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue(statusFilter);
  }, [brandId, statusFilter]);

  const handleDecision = async (itemId: string, status: "approved" | "rejected") => {
    try {
      await api.patch(`/dashboard/review-queue/${itemId}`, { status });
      // Optimistically remove the item from the list (it's no longer pending)
      setItems(prev => prev.filter(i => i.id !== itemId));
      setTotal(prev => Math.max(0, prev - 1));
    } catch {
      setError("Failed to update review item. Please try again.");
    }
  };

  const TAB_LABELS: { key: StatusFilter; label: string }[] = [
    { key: "pending", label: "Pending" },
    { key: "approved", label: "Approved" },
    { key: "rejected", label: "Rejected" },
  ];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Human Review Queue</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Articles flagged for manual review — low NLP confidence on sensitive categories
          for <span className="font-medium text-gray-700">{brandName}</span>
        </p>
      </div>

      {/* Status tabs */}
      <div className="flex border-b border-gray-200 mb-4">
        {TAB_LABELS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setStatusFilter(key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
              statusFilter === key
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            {label}
            {key === "pending" && total > 0 && statusFilter === "pending" && (
              <span className="ml-2 bg-amber-100 text-amber-700 text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                {total}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonRow key={i} />)}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <svg
            className="w-10 h-10 mx-auto mb-3 text-gray-300"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <div className="text-sm font-medium text-gray-500">
            No {statusFilter} items
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {statusFilter === "pending"
              ? "Articles are auto-queued when NLP confidence < 50% on crisis or regulatory categories."
              : `No ${statusFilter} reviews yet.`}
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map(item => (
            <QueueItemRow
              key={item.id}
              item={item}
              onDecision={handleDecision}
            />
          ))}
        </div>
      )}
    </div>
  );
}
