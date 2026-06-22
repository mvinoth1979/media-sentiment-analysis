const STEPS = [
  { icon: "📊", title: "Executive Overview", sub: "High level snapshot" },
  { icon: "🔍", title: "Source Level", sub: "Deep dive into sources" },
  { icon: "📄", title: "Mention Level", sub: "Article / Review level" },
  { icon: "⚡", title: "Insights & Action", sub: "Take action & track" },
];

export function DrillDownJourneyExample() {
  return (
    <div className="h-full flex flex-col bg-[#1a2744] border border-white/10 rounded-xl p-3 overflow-hidden">
      <div className="text-[11px] font-semibold text-white/70 mb-3 flex-none">Drill-Down Journey Example</div>
      <div className="flex items-center justify-between flex-1 min-h-0 gap-2">
        {STEPS.map((step, i) => (
          <div key={i} className="flex items-center gap-2 flex-1 min-w-0">
            <div className="flex flex-col items-center text-center min-w-0 flex-1">
              <div className="w-10 h-10 rounded-xl bg-blue-500/15 border border-blue-500/30 flex items-center justify-center mb-1.5 shrink-0">
                <span className="text-lg">{step.icon}</span>
              </div>
              <div className="text-[10px] font-semibold text-white/80 leading-tight">{step.title}</div>
              <div className="text-[8px] text-white/35 mt-0.5 leading-tight">{step.sub}</div>
            </div>
            {i < STEPS.length - 1 && (
              <svg className="w-4 h-4 text-white/20 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
