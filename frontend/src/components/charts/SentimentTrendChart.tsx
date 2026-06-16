import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, Label, ResponsiveContainer } from "recharts";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchAnnotations, createAnnotation } from "../../lib/api";
import type { TrendPoint, Annotation } from "../../lib/types";

interface Props {
  brandId: string;
  data: TrendPoint[];
}

export function SentimentTrendChart({ brandId, data }: Props) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [draftDate, setDraftDate] = useState("");
  const [draftLabel, setDraftLabel] = useState("");

  const { data: annotations = [] } = useQuery<Annotation[]>({
    queryKey: ["annotations", brandId],
    queryFn: () => fetchAnnotations(brandId),
    staleTime: 60_000,
  });

  const addAnnotation = useMutation({
    mutationFn: () => createAnnotation(brandId, draftDate, draftLabel.trim()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["annotations", brandId] });
      setDraftDate("");
      setDraftLabel("");
      setShowForm(false);
    },
  });

  const byDate = new Map<string, { sum: number; count: number }>();
  for (const d of data) {
    const date = d.time.slice(0, 10);
    const bucket = byDate.get(date) ?? { sum: 0, count: 0 };
    bucket.sum += d.value;
    bucket.count += 1;
    byDate.set(date, bucket);
  }
  const formatted = Array.from(byDate.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, { sum, count }]) => ({ date, score: Math.round(sum / count) }));
  const chartDates = new Set(formatted.map(p => p.date));

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-gray-200">Perception Score — 7 Days</div>
        <button
          onClick={() => setShowForm(s => !s)}
          className="text-xs text-indigo-400 hover:text-indigo-300"
        >
          {showForm ? "Cancel" : "+ Annotate"}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={e => { e.preventDefault(); if (draftDate && draftLabel.trim()) addAnnotation.mutate(); }}
          className="flex flex-wrap items-center gap-2 mb-3"
        >
          <input
            type="date"
            value={draftDate}
            onChange={e => setDraftDate(e.target.value)}
            required
            className="bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-300 px-2 py-1.5 focus:outline-none focus:border-indigo-500"
          />
          <input
            type="text"
            value={draftLabel}
            onChange={e => setDraftLabel(e.target.value)}
            placeholder="What happened on this date?"
            required
            className="bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-200 px-2.5 py-1.5 placeholder:text-gray-500 focus:outline-none focus:border-indigo-500 flex-1 min-w-[160px]"
          />
          <button
            type="submit"
            disabled={addAnnotation.isPending}
            className="text-xs px-3 py-1.5 bg-indigo-600 rounded-lg text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            Save
          </button>
        </form>
      )}

      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={formatted}>
          <XAxis
            dataKey="date"
            tickFormatter={d => new Date(d).toLocaleDateString("en-IN", { weekday: "short" })}
            tick={{ fill: "#6b7280", fontSize: 11 }}
          />
          <YAxis domain={[0, 100]} tick={{ fill: "#6b7280", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: "#1f2937", border: "none" }}
            labelFormatter={d => new Date(d).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" })}
          />
          <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} dot={false} />
          {annotations
            .filter(a => chartDates.has(a.date))
            .map(a => (
              <ReferenceLine key={a.id} x={a.date} stroke="#f59e0b" strokeDasharray="3 3">
                <Label value={a.label} position="insideTopLeft" fill="#f59e0b" fontSize={10} />
              </ReferenceLine>
            ))}
        </LineChart>
      </ResponsiveContainer>

      {annotations.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {annotations.map(a => (
            <span
              key={a.id}
              className="text-[10px] text-amber-400 bg-amber-900/20 border border-amber-800/40 rounded-full px-2 py-0.5"
            >
              {new Date(a.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })} · {a.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
