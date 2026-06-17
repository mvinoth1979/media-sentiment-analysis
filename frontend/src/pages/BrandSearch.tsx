import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchBrands } from "../lib/api";
import { BrandSetup } from "./BrandSetup";

interface Props {
  onSelect: (brandId: string, brandName: string) => void;
  isAdmin?: boolean;
}

export function BrandSearch({ onSelect, isAdmin }: Props) {
  const [q, setQ]               = useState("");
  const [showSetup, setShowSetup] = useState(false);

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
              <button
                key={b.id}
                onClick={() => onSelect(b.id, b.name)}
                className={`w-full text-left px-4 py-3 flex items-center justify-between hover:bg-gray-800 transition-colors ${
                  i > 0 ? "border-t border-gray-800" : ""
                }`}
              >
                <div>
                  <div className="text-sm font-medium text-gray-100">{b.name}</div>
                  <div className="text-xs text-gray-500 mt-0.5">Brand ID: {b.id.slice(0, 8)}…</div>
                </div>
                <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
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
