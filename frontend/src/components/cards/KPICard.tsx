interface Props {
  label: string;
  value: string | number;
  sub?: string;
  color?: "green" | "red" | "yellow" | "blue" | "purple";
}
const colors = {
  green: "text-green-400", red: "text-red-400",
  yellow: "text-yellow-400", blue: "text-blue-400", purple: "text-purple-400",
};
export function KPICard({ label, value, sub, color = "blue" }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">{label}</div>
      <div className={`text-3xl font-bold ${colors[color]}`}>{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}
