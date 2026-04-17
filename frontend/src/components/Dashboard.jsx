import { useEffect, useRef } from 'react';

/* ─── Icon SVGs (inline to avoid extra deps) ─── */
const icons = {
  heart_rate: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6">
      <path d="M3 12h4l3-9 4 18 3-9h4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  glucose: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6">
      <path d="M12 2C12 2 4 10 4 14a8 8 0 1016 0c0-4-8-12-8-12z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  steps: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6">
      <circle cx="12" cy="5" r="3" />
      <path d="M12 8v4m-3 3l3-3 3 3m-6 3l3-3 3 3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  sleep_hours: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6">
      <path d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
};

/* ─── Color mapping for each vital ─── */
const vitalMeta = {
  heart_rate: {
    label: 'Heart Rate',
    unit: 'BPM',
    icon: icons.heart_rate,
    gradient: 'from-rose-500 to-pink-600',
    ring: 'ring-rose-500/20',
    text: 'text-rose-400',
    getStatus: (v) => (v > 100 ? 'danger' : v > 85 ? 'warning' : 'normal'),
  },
  glucose: {
    label: 'Glucose',
    unit: 'mg/dL',
    icon: icons.glucose,
    gradient: 'from-amber-400 to-orange-500',
    ring: 'ring-amber-500/20',
    text: 'text-amber-400',
    getStatus: (v) => (v > 150 ? 'danger' : v > 120 ? 'warning' : 'normal'),
  },
  steps: {
    label: 'Steps',
    unit: 'steps',
    icon: icons.steps,
    gradient: 'from-emerald-400 to-teal-500',
    ring: 'ring-emerald-500/20',
    text: 'text-emerald-400',
    getStatus: (v) => (v < 2000 ? 'danger' : v < 5000 ? 'warning' : 'normal'),
  },
  sleep_hours: {
    label: 'Sleep',
    unit: 'hrs',
    icon: icons.sleep_hours,
    gradient: 'from-indigo-400 to-violet-500',
    ring: 'ring-indigo-500/20',
    text: 'text-indigo-400',
    getStatus: (v) => (v < 5 ? 'danger' : v < 6.5 ? 'warning' : 'normal'),
  },
};

const statusColors = {
  normal: 'bg-emerald-500',
  warning: 'bg-amber-500',
  danger: 'bg-rose-500',
};

/* ─── Individual vital card ─── */
function VitalCard({ vitalKey, value }) {
  const meta = vitalMeta[vitalKey];
  const status = meta.getStatus(value);
  const cardRef = useRef(null);

  // Flash animation on value change
  useEffect(() => {
    const el = cardRef.current;
    if (!el) return;
    el.classList.remove('vital-update');
    void el.offsetWidth; // reflow
    el.classList.add('vital-update');
  }, [value]);

  return (
    <div
      ref={cardRef}
      id={`vital-card-${vitalKey}`}
      className={`glass-card-hover p-5 relative overflow-hidden`}
    >
      {/* Gradient accent bar */}
      <div
        className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${meta.gradient}`}
      />

      <div className="flex items-center justify-between mb-3">
        <div className={`p-2 rounded-lg bg-white/5 ${meta.text}`}>
          {meta.icon}
        </div>
        <div className={`w-2.5 h-2.5 rounded-full ${statusColors[status]} animate-pulse`} />
      </div>

      <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
        {meta.label}
      </p>
      <p className="text-3xl font-bold tracking-tight">
        {value !== null && value !== undefined ? (
          <>
            {typeof value === 'number' ? value.toLocaleString() : value}
            <span className="text-sm font-normal text-slate-500 ml-1">{meta.unit}</span>
          </>
        ) : (
          <span className="text-slate-600">—</span>
        )}
      </p>
    </div>
  );
}

/* ─── Risk + Health Score bar ─── */
function ScoreBars({ riskScore, healthScore, healthGrade }) {
  const riskColor =
    riskScore > 70 ? 'bg-rose-500' : riskScore > 40 ? 'bg-amber-500' : 'bg-emerald-500';
  const riskLabel =
    riskScore > 70 ? 'High Risk' : riskScore > 40 ? 'Moderate' : 'Low Risk';

  const healthColor =
    healthScore >= 70 ? 'bg-emerald-500' : healthScore >= 45 ? 'bg-amber-500' : 'bg-rose-500';

  const gradeColors = {
    A: 'bg-emerald-500/20 text-emerald-400',
    B: 'bg-blue-500/20 text-blue-400',
    C: 'bg-amber-500/20 text-amber-400',
    D: 'bg-orange-500/20 text-orange-400',
    F: 'bg-rose-500/20 text-rose-400',
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 col-span-full">
      {/* Risk Score */}
      <div id="risk-score-bar" className="glass-card p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              AI Risk Score
            </p>
            <p className="text-2xl font-bold mt-1">
              {riskScore.toFixed(1)}
              <span className="text-sm font-normal text-slate-500 ml-1">/ 100</span>
            </p>
          </div>
          <span className={`text-xs font-semibold px-3 py-1 rounded-full ${
            riskScore > 70 ? 'bg-rose-500/20 text-rose-400' :
            riskScore > 40 ? 'bg-amber-500/20 text-amber-400' :
            'bg-emerald-500/20 text-emerald-400'
          }`}>{riskLabel}</span>
        </div>
        <div className="risk-track">
          <div className={`h-full rounded-full transition-all duration-700 ease-out ${riskColor}`}
            style={{ width: `${Math.min(riskScore, 100)}%` }} />
        </div>
      </div>

      {/* Health Score */}
      <div id="health-score-bar" className="glass-card p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              ❤️ Health Score
            </p>
            <p className="text-2xl font-bold mt-1">
              {healthScore.toFixed(0)}
              <span className="text-sm font-normal text-slate-500 ml-1">/ 100</span>
            </p>
          </div>
          {healthGrade && (
            <span className={`text-xs font-bold px-3 py-1 rounded-full ${gradeColors[healthGrade] || 'bg-white/10 text-slate-400'}`}>
              Grade {healthGrade}
            </span>
          )}
        </div>
        <div className="risk-track">
          <div className={`h-full rounded-full transition-all duration-700 ease-out ${healthColor}`}
            style={{ width: `${Math.min(healthScore, 100)}%` }} />
        </div>
      </div>
    </div>
  );
}

/* ─── Dashboard (exported) ─── */
export default function Dashboard({ vitals, riskScore, healthScore, healthGrade }) {
  const keys = ['heart_rate', 'glucose', 'steps', 'sleep_hours'];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {keys.map((k) => (
        <VitalCard key={k} vitalKey={k} value={vitals?.[k] ?? null} />
      ))}
      <div className="col-span-2 md:col-span-4">
        <ScoreBars
          riskScore={riskScore}
          healthScore={healthScore ?? 0}
          healthGrade={healthGrade}
        />
      </div>
    </div>
  );
}
