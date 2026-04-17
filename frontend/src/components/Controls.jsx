import { useState } from 'react';

export default function Controls({ apiBase, currentRisk }) {
  const [exerciseIncrease, setExerciseIncrease] = useState(false);
  const [betterSleep, setBetterSleep] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exercise_increase: exerciseIncrease,
          better_sleep: betterSleep,
        }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const riskChange = result?.risk_change ?? 0;
  const simulatedRisk = result?.simulated_risk ?? null;

  return (
    <div id="simulation-controls" className="glass-card p-6 flex flex-col gap-5">
      <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
        What-If Simulation
      </h2>

      {/* Toggles */}
      <div className="space-y-4">
        <Toggle
          id="toggle-exercise"
          label="Increase Exercise"
          description="30 % more daily steps, 15 % lower glucose"
          checked={exerciseIncrease}
          onChange={setExerciseIncrease}
          color="emerald"
        />
        <Toggle
          id="toggle-sleep"
          label="Better Sleep"
          description="20 % more sleep hours, 10 % lower heart rate"
          checked={betterSleep}
          onChange={setBetterSleep}
          color="indigo"
        />
      </div>

      {/* Run button */}
      <button
        id="run-simulation-btn"
        onClick={runSimulation}
        disabled={loading || (!exerciseIncrease && !betterSleep)}
        className={`
          w-full py-3 rounded-xl font-semibold text-sm transition-all duration-300
          ${
            !exerciseIncrease && !betterSleep
              ? 'bg-white/5 text-slate-600 cursor-not-allowed'
              : 'bg-gradient-to-r from-brand-500 to-brand-600 text-white hover:shadow-lg hover:shadow-brand-500/25 active:scale-[0.98]'
          }
        `}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
            Running…
          </span>
        ) : (
          'Run Simulation'
        )}
      </button>

      {/* Results */}
      {result && (
        <div className="space-y-3 animate-fade-in">
          <div className="h-px bg-white/10" />

          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Current Risk</span>
            <span className="text-sm font-bold">{result.current_risk?.toFixed(1)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Simulated Risk</span>
            <span className="text-sm font-bold">{simulatedRisk?.toFixed(1)}</span>
          </div>

          {/* Delta badge */}
          <div
            className={`flex items-center justify-center gap-2 py-2 rounded-xl text-sm font-bold ${
              riskChange < 0
                ? 'bg-emerald-500/15 text-emerald-400'
                : riskChange > 0
                ? 'bg-rose-500/15 text-rose-400'
                : 'bg-white/5 text-slate-400'
            }`}
          >
            {riskChange < 0 ? '↓' : riskChange > 0 ? '↑' : '→'}
            {' '}
            {Math.abs(riskChange).toFixed(1)} pts
            {riskChange < 0 ? ' improvement' : riskChange > 0 ? ' worse' : ' no change'}
          </div>

          {/* Adjusted vitals */}
          {result.adjusted_vitals && (
            <div className="text-xs text-slate-500 space-y-1 mt-2">
              <p className="text-slate-400 font-medium mb-1">Adjusted Vitals:</p>
              <Row label="Heart Rate" val={`${result.adjusted_vitals.heart_rate} BPM`} />
              <Row label="Glucose" val={`${result.adjusted_vitals.glucose} mg/dL`} />
              <Row label="Steps" val={result.adjusted_vitals.steps?.toLocaleString()} />
              <Row label="Sleep" val={`${result.adjusted_vitals.sleep_hours} hrs`} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Toggle component ─── */
function Toggle({ id, label, description, checked, onChange, color }) {
  const bg = checked
    ? color === 'emerald'
      ? 'bg-emerald-500'
      : 'bg-indigo-500'
    : 'bg-white/10';

  return (
    <label htmlFor={id} className="flex items-center justify-between gap-3 cursor-pointer group">
      <div>
        <p className="text-sm font-medium text-slate-200 group-hover:text-white transition-colors">
          {label}
        </p>
        <p className="text-xs text-slate-500">{description}</p>
      </div>
      <div className="relative flex-shrink-0">
        <input
          id={id}
          type="checkbox"
          className="sr-only"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
        />
        <div className={`w-11 h-6 rounded-full transition-colors duration-300 ${bg}`} />
        <div
          className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-300 ${
            checked ? 'translate-x-5' : ''
          }`}
        />
      </div>
    </label>
  );
}

/* ─── Tiny row helper ─── */
function Row({ label, val }) {
  return (
    <div className="flex justify-between">
      <span>{label}</span>
      <span className="text-slate-300">{val}</span>
    </div>
  );
}
