import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';

/* ─── Series config ─── */
const series = [
  { key: 'heart_rate', name: 'Heart Rate', color: '#f43f5e', yAxisId: 'left' },
  { key: 'glucose',    name: 'Glucose',    color: '#f59e0b', yAxisId: 'left' },
  { key: 'steps',      name: 'Steps',      color: '#10b981', yAxisId: 'right' },
  { key: 'sleep_hours',name: 'Sleep (hrs)',color: '#818cf8', yAxisId: 'left' },
];

/* ─── Custom tooltip ─── */
function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card p-3 text-xs space-y-1 border border-white/10">
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: p.color }}
          />
          <span className="text-slate-400">{p.name}:</span>
          <span className="font-semibold text-white">
            {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function Chart({ history }) {
  // Format data for recharts — use index as X label
  const data = history.map((d, i) => ({
    idx: i + 1,
    heart_rate: d.heart_rate,
    glucose: d.glucose,
    steps: d.steps,
    sleep_hours: d.sleep_hours,
  }));

  return (
    <div id="vitals-chart" className="glass-card p-6">
      <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
        Vitals Trend
        <span className="text-xs font-normal text-slate-500 ml-2">
          (last {data.length} readings)
        </span>
      </h2>

      {data.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-slate-600 text-sm">
          Waiting for data…
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="idx"
              tick={{ fill: '#64748b', fontSize: 11 }}
              axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
              tickLine={false}
            />
            <YAxis
              yAxisId="left"
              tick={{ fill: '#64748b', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              domain={['auto', 'auto']}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fill: '#64748b', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="top"
              wrapperStyle={{ paddingBottom: 12, fontSize: 12, color: '#94a3b8' }}
            />
            {series.map((s) => (
              <Line
                key={s.key}
                yAxisId={s.yAxisId}
                type="monotone"
                dataKey={s.key}
                name={s.name}
                stroke={s.color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0 }}
                animationDuration={400}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
