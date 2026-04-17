import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
  ReferenceLine,
} from 'recharts';

/* ─── Series config for projected vitals ─── */
const series = [
  { key: 'heart_rate', name: 'Heart Rate', color: '#f43f5e', baseColor: '#f43f5e50' },
  { key: 'glucose', name: 'Glucose', color: '#f59e0b', baseColor: '#f59e0b50' },
  { key: 'steps', name: 'Steps', color: '#10b981', baseColor: '#10b98150' },
  { key: 'sleep_hours', name: 'Sleep (hrs)', color: '#818cf8', baseColor: '#818cf850' },
];

/* ─── Custom tooltip ─── */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card p-3 text-xs space-y-1 border border-white/10">
      <p className="text-slate-400 font-semibold mb-1">Day {label}</p>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: p.color || p.stroke }}
          />
          <span className="text-slate-400">{p.name}:</span>
          <span className="font-semibold text-white">
            {typeof p.value === 'number' ? p.value.toLocaleString(undefined, { maximumFractionDigits: 1 }) : p.value}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function SimulationChart({ futureVitals, baselineVitals }) {
  if (!futureVitals?.length) return null;

  // Prepend day 0 (baseline) and format data
  const data = [
    {
      day: 0,
      heart_rate: baselineVitals.heart_rate,
      glucose: baselineVitals.glucose,
      steps: baselineVitals.steps,
      sleep_hours: baselineVitals.sleep_hours,
    },
    ...futureVitals,
  ];

  // Separate charts: one for HR+Glucose (left scale), one for Steps+Sleep
  // Actually, let's do a tabbed approach with individual mini-charts for clarity

  return (
    <div className="glass-card p-6 space-y-4">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4 text-brand-400">
          <path d="M3 3v18h18" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M7 16l4-8 4 4 4-10" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Projected Vitals Over {futureVitals.length} Days
      </h3>

      {/* 2×2 grid of mini-charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {series.map((s) => {
          const baselineVal = baselineVitals[s.key];
          return (
            <div key={s.key} className="bg-white/[0.03] rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold" style={{ color: s.color }}>
                  {s.name}
                </span>
                <div className="flex items-center gap-2 text-[10px] text-slate-500">
                  <span>Start: {typeof baselineVal === 'number' ? baselineVal.toLocaleString(undefined, { maximumFractionDigits: 1 }) : baselineVal}</span>
                  <span>→</span>
                  <span className="text-white font-medium">
                    End: {data[data.length - 1][s.key]?.toLocaleString(undefined, { maximumFractionDigits: 1 })}
                  </span>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={140}>
                <AreaChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
                  <defs>
                    <linearGradient id={`grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={s.color} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={s.color} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis
                    dataKey="day"
                    tick={{ fill: '#475569', fontSize: 10 }}
                    axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#475569', fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    domain={['auto', 'auto']}
                    width={35}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine
                    y={baselineVal}
                    stroke={s.color}
                    strokeDasharray="4 4"
                    strokeOpacity={0.4}
                  />
                  <Area
                    type="monotone"
                    dataKey={s.key}
                    name={s.name}
                    stroke={s.color}
                    strokeWidth={2}
                    fill={`url(#grad-${s.key})`}
                    dot={false}
                    activeDot={{ r: 3, strokeWidth: 0, fill: s.color }}
                    animationDuration={800}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          );
        })}
      </div>
    </div>
  );
}
