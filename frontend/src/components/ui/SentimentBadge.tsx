const styles = {
  positive: "bg-green-900/40 text-green-400 border border-green-800",
  negative: "bg-red-900/40 text-red-400 border border-red-800",
  neutral:  "bg-yellow-900/40 text-yellow-400 border border-yellow-800",
};
export function SentimentBadge({ label }: { label: "positive" | "negative" | "neutral" }) {
  return <span className={`text-xs px-2 py-0.5 rounded ${styles[label]}`}>{label}</span>;
}
