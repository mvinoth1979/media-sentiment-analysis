import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchBrands, deleteBrand } from "../lib/api";
import { BrandSetup } from "./BrandSetup";

interface Props {
  onSelect: (brandId: string, brandName: string) => void;
  isAdmin?: boolean;
  isMasterAdmin?: boolean;
}

export function BrandSearch({ onSelect, isAdmin, isMasterAdmin }: Props) {
  const [q, setQ]                 = useState("");
  const [showSetup, setShowSetup] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: (brandId: string) => deleteBrand(brandId),
    onSuccess: () => {
      setConfirmDelete(null);
      queryClient.invalidateQueries({ queryKey: ["brands"] });
    },
  });

  const { data: brands = [], isLoading } = useQuery({
    queryKey: ["brands", q],
    queryFn: () => fetchBrands(q),
    staleTime: 30_000,
  });

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="w-full max-w-md space-y-6 px-4">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-100">Brand Report</h2>
            <p className="text-sm text-gray-500 mt-1">Search for a brand to view its media sentiment report</p>
          </div>
          {isAdmin && (
            <button
              onClick={() => setShowSetup(true)}
              className="shrink-0 mt-1 flex items-center gap-1.5 text-xs px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Brand
            </button>
          )}
        </div>

        <div className="relative">
          <input
            type="text"
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="Type a brand name…"
            autoFocus
            className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-indigo-500 transition-colors"
          />
          {isLoading && (
            <div className="absolute right-3 top-3 text-gray-600 text-xs">searching…</div>
          )}
        </div>

        {brands.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            {brands.map((b, i) => (
              <div key={b.id} className={`flex items-center ${i > 0 ? "border-t border-gray-800" : ""}`}>
                {confirmDelete === b.id ? (
                  <div className="flex-1 px-4 py-3 flex items-center gap-3 bg-red-950/30">
                    <span className="text-xs text-red-300 flex-1">
                      Delete <strong>{b.name}</strong> and ALL its articles? This cannot be undone.
                    </span>
                    <button
                      onClick={() => deleteMutation.mutate(b.id)}
                      disabled={deleteMutation.isPending}
                      className="text-xs px-2.5 py-1 bg-red-700 hover:bg-red-600 text-white rounded disabled:opacity-50"
                    >
                      {deleteMutation.isPending ? "Deleting…" : "Delete"}
                    </button>
                    <button onClick={() => setConfirmDelete(null)} className="text-xs text-gray-400 hover:text-gray-200">
                      Cancel
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => onSelect(b.id, b.name)}
                      className="flex-1 text-left px-4 py-3 flex items-center justify-between hover:bg-gray-800 transition-colors"
                    >
                      <div>
                        <div className="text-sm font-medium text-gray-100">{b.name}</div>
                        <div className="text-xs text-gray-500 mt-0.5">Brand ID: {b.id.slice(0, 8)}…</div>
                      </div>
                      <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                    {isMasterAdmin && (
                      <button
                        onClick={() => setConfirmDelete(b.id)}
                        className="px-3 py-3 text-gray-600 hover:text-red-400 transition-colors"
                        title="Delete brand"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        )}

        {!isLoading && q.length > 0 && brands.length === 0 && (
          <p className="text-sm text-gray-500 text-center">No brands found for "{q}"</p>
        )}

        {q.length === 0 && brands.length > 0 && (
          <p className="text-xs text-gray-600 text-center">Showing all brands — type to filter</p>
        )}
      </div>

      {showSetup && (
        <BrandSetup
          onSuccess={(id, name) => {
            setShowSetup(false);
            onSelect(id, name);
          }}
          onClose={() => setShowSetup(false)}
        />
      )}
    </div>
  );
}
