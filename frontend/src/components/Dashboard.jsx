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
    fullLabel: 'Heart Rate (BPM)',
    icon: icons.heart_rate,
    gradient: 'from-rose-500 to-pink-600',
    ring: 'ring-rose-500/20',
    text: 'text-rose-400',
    tooltip: 'Optimal resting HR: 60–72 BPM (AHA). >100 = tachycardia risk.',
    getStatus: (v) => {
      if (v > 100) return { status: 'danger', label: 'Elevated' };
      if (v > 85) return { status: 'warning', label: 'Above Normal' };
      return { status: 'normal', label: 'Normal' };
    },
  },
  glucose: {
    label: 'Blood Glucose',
    unit: 'mg/dL',
    fullLabel: 'Blood Glucose (mg/dL)',
    icon: icons.glucose,
    gradient: 'from-amber-400 to-orange-500',
    ring: 'ring-amber-500/20',
    text: 'text-amber-400',
    tooltip: 'Normal fasting: 70–100 mg/dL. Pre-diabetic: 100–125. Diabetic: ≥126 (ADA).',
    getStatus: (v) => {
      if (v > 150) return { status: 'danger', label: 'High' };
      if (v > 120) return { status: 'warning', label: 'Borderline' };
      return { status: 'normal', label: 'Normal' };
    },
  },
  steps: {
    label: 'Daily Steps',
    unit: 'steps',
    fullLabel: 'Daily Steps',
    icon: icons.steps,
    gradient: 'from-emerald-400 to-teal-500',
    ring: 'ring-emerald-500/20',
    text: 'text-emerald-400',
    tooltip: 'Target: 7,000–10,000 steps/day (WHO). <3,000 = sedentary risk.',
    getStatus: (v) => {
      if (v < 2000) return { status: 'danger', label: 'Sedentary' };
      if (v < 5000) return { status: 'warning', label: 'Low Activity' };
      return { status: 'normal', label: 'Active' };
    },
  },
  sleep_hours: {
    label: 'Sleep Duration',
    unit: 'hours',
    fullLabel: 'Sleep Duration (hours)',
    icon: icons.sleep_hours,
    gradient: 'from-indigo-400 to-violet-500',
    ring: 'ring-indigo-500/20',
    text: 'text-indigo-400',
    tooltip: 'Optimal: 7–9 hours (NSF). <6 hrs impairs glucose tolerance.',
    getStatus: (v) => {
      if (v < 5) return { status: 'danger', label: 'Deprived' };
      if (v < 6.5) return { status: 'warning', label: 'Insufficient' };
      return { status: 'normal', label: 'Optimal' };
    },
  },
};

const statusColors = {
  normal: 'bg-emerald-500',
  warning: 'bg-amber-500',
  danger: 'bg-rose-500',
};

const statusTextColors = {
  normal: 'text-emerald-400 bg-emerald-500/15',
  warning: 'text-amber-400 bg-amber-500/15',
  danger: 'text-rose-400 bg-rose-500/15',
};

/* ─── Individual vital card with tooltip and status label ─── */
function VitalCard({ vitalKey, value, trendInfo }) {
  const meta = vitalMeta[vitalKey];
  const { status, label: statusLabel } = value != null ? meta.getStatus(value) : { status: 'normal', label: '—' };
  const cardRef = useRef(null);

  useEffect(() => {
    const el = cardRef.current;
    if (!el) return;
    el.classList.remove('vital-update');
    void el.offsetWidth;
    el.classList.add('vital-update');
  }, [value]);

  return (
    <div
      ref={cardRef}
      id={`vital-card-${vitalKey}`}
      className="glass-card-hover p-5 relative overflow-hidden group"
      title={meta.tooltip}
    >
      {/* Gradient accent bar */}
      <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${meta.gradient}`} />

      {/* Tooltip (visible on hover) */}
      <div className="absolute top-10 left-3 right-3 z-20 opacity-0 group-hover:opacity-100
        transition-opacity duration-300 pointer-events-none">
        <div className="bg-slate-900/95 border border-white/10 rounded-lg p-2.5 text-[10px] text-slate-300 leading-relaxed shadow-xl">
          {meta.tooltip}
        </div>
      </div>

      <div className="flex items-center justify-between mb-3">
        <div className={`p-2 rounded-lg bg-white/5 ${meta.text}`}>
          {meta.icon}
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[9px] font-semibold px-2 py-0.5 rounded-full ${statusTextColors[status]}`}>
            {statusLabel}
          </span>
          <div className={`w-2.5 h-2.5 rounded-full ${statusColors[status]} animate-pulse`} />
        </div>
      </div>

      <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
        {meta.fullLabel}
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

      {/* Mini trend indicator */}
      {trendInfo && (
        <p className={`text-[10px] mt-1.5 font-medium ${
          trendInfo.direction === 'increasing' ? (
            vitalKey === 'steps' || vitalKey === 'sleep_hours' ? 'text-emerald-500' : 'text-rose-400'
          ) : trendInfo.direction === 'decreasing' ? (
            vitalKey === 'steps' || vitalKey === 'sleep_hours' ? 'text-rose-400' : 'text-emerald-500'
          ) : 'text-slate-500'
        }`}>
          {trendInfo.direction === 'increasing' ? '↑' :
           trendInfo.direction === 'decreasing' ? '↓' : '→'}
          {' '}{Math.abs(trendInfo.percent_change)}% from avg
        </p>
      )}
    </div>
  );
}

/* ─── Disease Classification Badge ─── */
function DiseaseBadge({ classification, confidence }) {
  if (!classification) return null;

  const colorMap = {
    'Normal': 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25',
    'Pre-Diabetic': 'bg-amber-500/15 text-amber-400 border-amber-500/25',
    'Diabetic': 'bg-rose-500/15 text-rose-400 border-rose-500/25',
    'High Cardiovascular Risk': 'bg-red-500/15 text-red-400 border-red-500/25',
  };

  const iconMap = {
    'Normal': '✓',
    'Pre-Diabetic': '⚠',
    'Diabetic': '🔴',
    'High Cardiovascular Risk': '❤️‍🩹',
  };

  return (
    <div className={`glass-card p-4 border ${colorMap[classification] || 'bg-white/5 text-slate-400 border-white/10'}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium mb-1">
            🏥 Disease Classification (ML)
          </p>
          <p className="text-sm font-bold flex items-center gap-1.5">
            <span>{iconMap[classification] || '•'}</span>
            {classification}
          </p>
        </div>
        {confidence != null && (
          <div className="text-right">
            <p className="text-[10px] text-slate-500">Model Confidence</p>
            <p className="text-lg font-bold tabular-nums">{(confidence * 100).toFixed(0)}%</p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Health Score Progression ─── */
function HealthProgression({ progression }) {
  if (!progression) return null;

  return (
    <div className={`flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-lg ${
      progression.direction === 'improved'
        ? 'bg-emerald-500/10 text-emerald-400'
        : 'bg-rose-500/10 text-rose-400'
    }`}>
      <span>{progression.direction === 'improved' ? '📈' : '📉'}</span>
      <span>
        Health Score: {progression.from} → {progression.to}
        ({progression.change > 0 ? '+' : ''}{progression.change})
      </span>
    </div>
  );
}

/* ─── Risk + Health Score bars ─── */
function ScoreBars({ riskScore, healthScore, healthGrade, hsProgression }) {
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
              🧠 AI Risk Score
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
          <div className="flex items-center gap-2">
            {healthGrade && (
              <span className={`text-xs font-bold px-3 py-1 rounded-full ${gradeColors[healthGrade] || 'bg-white/10 text-slate-400'}`}>
                Grade {healthGrade}
              </span>
            )}
          </div>
        </div>
        <div className="risk-track">
          <div className={`h-full rounded-full transition-all duration-700 ease-out ${healthColor}`}
            style={{ width: `${Math.min(healthScore, 100)}%` }} />
        </div>
        {/* Health Score Progression */}
        {hsProgression && (
          <div className="mt-2">
            <HealthProgression progression={hsProgression} />
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Dashboard (exported) ─── */
export default function Dashboard({
  vitals, riskScore, healthScore, healthGrade,
  diseaseClassification, diseaseConfidence,
  trendData, hsProgression,
}) {
  const keys = ['heart_rate', 'glucose', 'steps', 'sleep_hours'];

  // Extract per-vital trend info from trendData
  const getTrendInfo = (key) => {
    if (!trendData?.trends?.[key]) return null;
    return trendData.trends[key];
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {keys.map((k) => (
        <VitalCard
          key={k}
          vitalKey={k}
          value={vitals?.[k] ?? null}
          trendInfo={getTrendInfo(k)}
        />
      ))}

      {/* Disease Classification Badge */}
      <div className="col-span-2 md:col-span-4">
        <DiseaseBadge
          classification={diseaseClassification}
          confidence={diseaseConfidence}
        />
      </div>

      {/* Score Bars */}
      <div className="col-span-2 md:col-span-4">
        <ScoreBars
          riskScore={riskScore}
          healthScore={healthScore ?? 0}
          healthGrade={healthGrade}
          hsProgression={hsProgression}
        />
      </div>
    </div>
  );
}
