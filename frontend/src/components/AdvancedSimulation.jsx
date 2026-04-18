import { useState } from 'react';
import SimulationChart from './SimulationChart';

const API_BASE = 'http://localhost:8000';

const DEFAULT_PROFILE = {
  age: 35,
  weight_kg: 75,
  height_cm: 170,
  conditions: [],
};

const CONDITION_OPTIONS = ['diabetes', 'hypertension', 'obesity'];

export default function AdvancedSimulation({ currentRisk }) {
  const [profile, setProfile] = useState({ ...DEFAULT_PROFILE });
  const [exerciseMin, setExerciseMin] = useState(30);
  const [sleepHrs, setSleepHrs] = useState(7);
  const [calories, setCalories] = useState(2200);
  const [simDays, setSimDays] = useState(14);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const toggleCondition = (cond) => {
    setProfile((p) => ({
      ...p,
      conditions: p.conditions.includes(cond)
        ? p.conditions.filter((c) => c !== cond)
        : [...p.conditions, cond],
    }));
  };

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/simulate-advanced`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient: profile,
          exercise_minutes: exerciseMin,
          sleep_hours: sleepHrs,
          calorie_intake: calories,
          simulation_days: simDays,
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

  const riskBefore = result?.risk_before?.risk_score ?? currentRisk;
  const riskAfter = result?.risk_after?.risk_score ?? null;
  const improvement = result?.improvement_percent ?? null;
  const segment = result?.patient_segment;
  const hsBefore = result?.health_score_before;
  const hsAfter = result?.health_score_after;
  const diseaseClassification = result?.disease_classification ?? result?.risk_before?.disease_classification;

  return (
    <div className="space-y-6">
      {/* ─── Controls Panel ─── */}
      <div id="advanced-simulation" className="glass-card p-6 space-y-5">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4 text-brand-400">
            <path d="M9.5 2A2.5 2.5 0 0112 4.5v15a2.5 2.5 0 01-4.96.44M14.5 2A2.5 2.5 0 0012 4.5" strokeLinecap="round" />
            <path d="M4.2 5.5A9.96 9.96 0 002 12c0 5.52 4.48 10 10 10s10-4.48 10-10S17.52 2 12 2" strokeLinecap="round" />
          </svg>
          Clinical Simulation Engine
        </h2>

        {/* Patient Profile */}
        <div className="space-y-3">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Patient Profile</p>
          <div className="grid grid-cols-3 gap-3">
            <NumberInput label="Age (years)" value={profile.age} min={18} max={90} unit="yrs"
              onChange={(v) => setProfile((p) => ({ ...p, age: v }))} />
            <NumberInput label="Weight (kg)" value={profile.weight_kg} min={30} max={250} unit="kg"
              onChange={(v) => setProfile((p) => ({ ...p, weight_kg: v }))} />
            <NumberInput label="Height (cm)" value={profile.height_cm} min={100} max={230} unit="cm"
              onChange={(v) => setProfile((p) => ({ ...p, height_cm: v }))} />
          </div>
          <div className="flex flex-wrap gap-2">
            {CONDITION_OPTIONS.map((cond) => (
              <button key={cond} onClick={() => toggleCondition(cond)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                  profile.conditions.includes(cond)
                    ? 'bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/30'
                    : 'bg-white/5 text-slate-500 hover:bg-white/10 hover:text-slate-300'
                }`}>
                {cond.charAt(0).toUpperCase() + cond.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="h-px bg-white/10" />

        {/* Sliders */}
        <div className="space-y-4">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Lifestyle Interventions</p>
          <Slider id="exercise-slider" label="Exercise" value={exerciseMin} min={0} max={90}
            unit="min/day" onChange={setExerciseMin} color="emerald" icon="🏃" />
          <Slider id="sleep-slider" label="Sleep Target" value={sleepHrs} min={4} max={9}
            step={0.5} unit="hrs/night" onChange={setSleepHrs} color="indigo" icon="🌙" />
          <Slider id="calorie-slider" label="Calorie Intake" value={calories} min={1200} max={3500}
            step={100} unit="kcal/day" onChange={setCalories} color="amber" icon="🍽️" />
        </div>

        <div className="h-px bg-white/10" />

        {/* Duration */}
        <div className="space-y-2">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Simulation Duration</p>
          <div className="flex gap-2">
            {[7, 14, 30, 60].map((d) => (
              <button key={d} onClick={() => setSimDays(d)}
                className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all duration-200 ${
                  simDays === d
                    ? 'bg-brand-500/20 text-brand-400 ring-1 ring-brand-500/30'
                    : 'bg-white/5 text-slate-500 hover:bg-white/10'
                }`}>
                {d} days
              </button>
            ))}
          </div>
        </div>

        {/* Run */}
        <button id="run-advanced-simulation" onClick={runSimulation} disabled={loading}
          className="w-full py-3.5 rounded-xl font-semibold text-sm transition-all duration-300
            bg-gradient-to-r from-brand-500 to-brand-600 text-white
            hover:shadow-lg hover:shadow-brand-500/25 active:scale-[0.98]
            disabled:opacity-50 disabled:cursor-not-allowed">
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              Analyzing {simDays} days…
            </span>
          ) : `Run ${simDays}-Day Simulation`}
        </button>
      </div>

      {/* ═══ RESULTS ═══ */}
      {result && (
        <div className="space-y-4 animate-fade-in">

          {/* ── Baseline Vitals Being Analyzed ── */}
          {result.baseline_vitals && (
            <div className="glass-card p-4 space-y-2">
              <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                📋 Analyzing Current Vitals
              </h3>
              <div className="grid grid-cols-4 gap-2 text-center">
                {[
                  { label: 'Heart Rate', key: 'heart_rate', unit: 'BPM', icon: '💓' },
                  { label: 'Glucose', key: 'glucose', unit: 'mg/dL', icon: '🩸' },
                  { label: 'Steps', key: 'steps', unit: 'steps', icon: '👟' },
                  { label: 'Sleep', key: 'sleep_hours', unit: 'hrs', icon: '🌙' },
                ].map(v => (
                  <div key={v.key} className="bg-white/[0.03] rounded-lg p-2">
                    <p className="text-[10px] text-slate-500">{v.icon} {v.label}</p>
                    <p className="text-sm font-bold">
                      {result.baseline_vitals[v.key]?.toLocaleString(undefined, { maximumFractionDigits: 1 })}
                      <span className="text-[9px] text-slate-600 ml-0.5">{v.unit}</span>
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Disease Classification ── */}
          {diseaseClassification && (
            <div className={`glass-card p-4 border-l-4 ${
              diseaseClassification.classification === 'Normal' ? 'border-emerald-500' :
              diseaseClassification.classification === 'Pre-Diabetic' ? 'border-amber-500' :
              diseaseClassification.classification === 'Diabetic' ? 'border-rose-500' :
              'border-red-500'
            }`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Disease Classification</p>
                  <p className="text-sm font-bold mt-0.5">{diseaseClassification.classification}</p>
                </div>
                <div className="text-right">
                  <p className="text-[10px] text-slate-500">
                    {diseaseClassification.method === 'ml' ? 'ML Model' : 'Rule-Based'}
                  </p>
                  <p className="text-lg font-bold">
                    {(diseaseClassification.confidence * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
              {diseaseClassification.probabilities && Object.keys(diseaseClassification.probabilities).length > 0 && (
                <div className="flex gap-1 mt-2 flex-wrap">
                  {Object.entries(diseaseClassification.probabilities)
                    .sort(([,a], [,b]) => b - a)
                    .map(([label, prob]) => (
                      <span key={label} className={`text-[9px] px-2 py-0.5 rounded-full ${
                        prob > 0.5 ? 'bg-white/10 text-white font-semibold' : 'bg-white/5 text-slate-500'
                      }`}>
                        {label}: {(prob * 100).toFixed(0)}%
                      </span>
                    ))}
                </div>
              )}
            </div>
          )}

          {/* ── Patient Segment Badge ── */}
          {segment && (
            <div className={`glass-card p-4 border-l-4 ${
              segment.segment_color === 'rose' ? 'border-rose-500' :
              segment.segment_color === 'amber' ? 'border-amber-500' :
              segment.segment_color === 'yellow' ? 'border-yellow-500' :
              'border-emerald-500'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className={`text-xs font-bold uppercase tracking-wider ${
                    segment.segment_color === 'rose' ? 'text-rose-400' :
                    segment.segment_color === 'amber' ? 'text-amber-400' :
                    segment.segment_color === 'yellow' ? 'text-yellow-400' :
                    'text-emerald-400'
                  }`}>
                    {segment.segment}
                  </span>
                  <p className="text-[11px] text-slate-500 mt-0.5">{segment.monitoring_frequency}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  segment.segment_color === 'rose' ? 'bg-rose-500/15 text-rose-400' :
                  segment.segment_color === 'amber' ? 'bg-amber-500/15 text-amber-400' :
                  segment.segment_color === 'yellow' ? 'bg-yellow-500/15 text-yellow-400' :
                  'bg-emerald-500/15 text-emerald-400'
                }`}>
                  {segment.risk_factors?.length || 0} risk factors
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{segment.segment_description}</p>
              {segment.risk_factors?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {segment.risk_factors.map((rf, i) => (
                    <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-white/5 text-slate-500">
                      {rf}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── Health Score Before/After ── */}
          {hsBefore && hsAfter && (
            <div className="glass-card p-5 space-y-3">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                ❤️ Health Score Progression
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <HealthScoreCard label="Before" data={hsBefore} />
                <HealthScoreCard label="After" data={hsAfter} />
              </div>
              {/* Score change highlight */}
              <div className={`flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold ${
                hsAfter.health_score > hsBefore.health_score
                  ? 'bg-emerald-500/10 text-emerald-400'
                  : hsAfter.health_score < hsBefore.health_score
                  ? 'bg-rose-500/10 text-rose-400'
                  : 'bg-white/5 text-slate-400'
              }`}>
                📈 Health Score: {hsBefore.health_score.toFixed(0)} → {hsAfter.health_score.toFixed(0)}
                {hsAfter.health_score > hsBefore.health_score ? ' (Improved!)' :
                 hsAfter.health_score < hsBefore.health_score ? ' (Declined)' : ' (Stable)'}
              </div>
              {/* Component breakdown */}
              <div className="space-y-1.5 mt-2">
                <p className="text-[10px] font-medium text-slate-500 uppercase">Component Scores (After)</p>
                {Object.entries(hsAfter.component_scores)
                  .sort(([,a],[,b]) => b - a)
                  .map(([key, val]) => (
                    <div key={key} className="flex items-center gap-2">
                      <span className="text-[10px] text-slate-500 w-28 truncate capitalize">
                        {key.replace(/_/g, ' ')}
                      </span>
                      <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <div className={`h-full rounded-full transition-all duration-500 ${
                          val >= 70 ? 'bg-emerald-500' : val >= 45 ? 'bg-amber-500' : 'bg-rose-500'
                        }`} style={{ width: `${val}%` }} />
                      </div>
                      <span className="text-[10px] text-slate-400 w-8 text-right">{val}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* ── Risk Assessment ── */}
          <div className="glass-card p-5 space-y-4">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              🧠 Risk Assessment
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <RiskCard label="Before" score={riskBefore} level={result.risk_before?.risk_level}
                confidence={result.risk_before?.confidence} />
              <RiskCard label="After" score={riskAfter} level={result.risk_after?.risk_level}
                confidence={result.risk_after?.confidence} />
            </div>

            {improvement !== null && (
              <div className={`flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-bold ${
                improvement > 0 ? 'bg-emerald-500/15 text-emerald-400' :
                improvement < 0 ? 'bg-rose-500/15 text-rose-400' :
                'bg-white/5 text-slate-400'
              }`}>
                {improvement > 0 ? '↓' : improvement < 0 ? '↑' : '→'}{' '}
                {Math.abs(improvement).toFixed(1)}% risk {improvement > 0 ? 'reduction' : improvement < 0 ? 'increase' : 'change'}
              </div>
            )}

            {result.risk_after?.feature_contributions && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-slate-500">Risk Factor Breakdown</p>
                {Object.entries(result.risk_after.feature_contributions)
                  .sort(([,a],[,b]) => b - a).slice(0, 5)
                  .map(([key, pct]) => (
                    <div key={key} className="flex items-center gap-2">
                      <span className="text-xs text-slate-500 w-28 truncate capitalize">{key.replace(/_/g, ' ')}</span>
                      <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <div className="h-full rounded-full bg-brand-500 transition-all duration-500"
                          style={{ width: `${Math.min(pct, 100)}%` }} />
                      </div>
                      <span className="text-xs text-slate-400 w-10 text-right">{pct}%</span>
                    </div>
                  ))}
              </div>
            )}
          </div>

          {/* ── Trend Intelligence (NEW) ── */}
          {result.trend_intelligence?.length > 0 && (
            <div className="glass-card p-5 space-y-3">
              <h3 className="text-xs font-semibold text-brand-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>📈</span> Trend Intelligence
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {result.trend_intelligence.map((t, i) => (
                  <div key={i} className={`bg-white/[0.03] rounded-lg p-3 space-y-1 border-l-2 ${
                    t.is_positive === true ? 'border-emerald-500' :
                    t.is_positive === false ? 'border-rose-500' :
                    'border-slate-600'
                  }`}>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-500 font-medium">{t.label}</span>
                      <span className={`text-xs font-bold ${
                        t.is_positive === true ? 'text-emerald-400' :
                        t.is_positive === false ? 'text-rose-400' :
                        'text-slate-400'
                      }`}>
                        {t.icon} {Math.abs(t.percent_change)}%
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400">
                      {t.before} → {t.after} {t.unit}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Intervention Impact Score (NEW) ── */}
          {result.intervention_impact?.length > 0 && (
            <div className="glass-card p-5 space-y-3">
              <h3 className="text-xs font-semibold text-brand-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>🎯</span> Intervention Impact
              </h3>
              <div className="space-y-2.5">
                {result.intervention_impact.map((impact, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-lg">{impact.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold text-slate-300">{impact.intervention}</span>
                        <span className={`text-xs font-bold ${
                          impact.is_primary ? 'text-brand-400' : 'text-slate-400'
                        }`}>
                          {impact.contribution_percent}%
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                        <div className={`h-full rounded-full transition-all duration-700 ${
                          impact.is_primary ? 'bg-brand-500' : 'bg-slate-600'
                        }`} style={{ width: `${impact.contribution_percent}%` }} />
                      </div>
                      <p className="text-[10px] text-slate-500 mt-0.5">{impact.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Stability Indicator (NEW) ── */}
          {result.stability_indicator && (
            <div className={`glass-card p-4 flex items-center justify-between ${
              result.stability_indicator.status === 'Stable' ? 'border border-emerald-500/20' :
              result.stability_indicator.status === 'Moderate' ? 'border border-amber-500/20' :
              'border border-rose-500/20'
            }`}>
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Projection Stability</p>
                <p className={`text-sm font-bold ${
                  result.stability_indicator.status === 'Stable' ? 'text-emerald-400' :
                  result.stability_indicator.status === 'Moderate' ? 'text-amber-400' :
                  'text-rose-400'
                }`}>
                  {result.stability_indicator.status === 'Stable' ? '✓' :
                   result.stability_indicator.status === 'Moderate' ? '~' : '⚠'}{' '}
                  {result.stability_indicator.status}
                </p>
              </div>
              <div className="flex gap-1.5">
                {Object.entries(result.stability_indicator.detail || {}).map(([key, info]) => (
                  <span key={key} className={`text-[9px] px-1.5 py-0.5 rounded ${
                    info.stability === 'stable' ? 'bg-emerald-500/15 text-emerald-400' :
                    info.stability === 'moderate' ? 'bg-amber-500/15 text-amber-400' :
                    'bg-rose-500/15 text-rose-400'
                  }`}>
                    {key.replace(/_/g, ' ').split(' ').map(w => w[0]).join('').toUpperCase()}:{info.cv_percent}%
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* ── Early Warnings ── */}
          {result.early_warnings?.length > 0 && (
            <div className="glass-card p-5 space-y-2">
              <h3 className="text-xs font-semibold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>🚨</span> Early Warnings
              </h3>
              {result.early_warnings.map((w, i) => (
                <div key={i} className={`px-3 py-2.5 rounded-lg space-y-1 ${
                  w.level === 'critical' ? 'bg-rose-500/10 border border-rose-500/20' :
                  w.level === 'warning' ? 'bg-amber-500/10 border border-amber-500/20' :
                  'bg-blue-500/10 border border-blue-500/20'
                }`}>
                  <p className={`text-xs font-semibold ${
                    w.level === 'critical' ? 'text-rose-400' :
                    w.level === 'warning' ? 'text-amber-400' : 'text-blue-400'
                  }`}>{w.title}</p>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{w.message}</p>
                  <p className="text-[10px] text-slate-500 italic">→ {w.action}</p>
                </div>
              ))}
            </div>
          )}

          {/* ── Anomaly Alerts ── */}
          {result.anomalies?.length > 0 && (
            <div className="glass-card p-5 space-y-2">
              <h3 className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>⚠️</span> Anomaly Alerts
              </h3>
              {result.anomalies.map((a, i) => (
                <div key={i} className={`text-xs px-3 py-2 rounded-lg ${
                  a.severity === 'critical' ? 'bg-rose-500/10 text-rose-400' : 'bg-amber-500/10 text-amber-400'
                }`}>{a.message}</div>
              ))}
            </div>
          )}

          {/* ── Recommendations ── */}
          {result.recommendations?.length > 0 && (
            <div className="glass-card p-5 space-y-3">
              <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>💊</span> Personalized Recommendations
              </h3>
              {result.recommendations.map((rec, i) => (
                <div key={i} className="bg-white/[0.03] rounded-xl p-3 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${
                      rec.priority === 'high' ? 'bg-rose-500/20 text-rose-400' :
                      rec.priority === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>{rec.priority}</span>
                    <span className="text-[10px] text-slate-600 capitalize">{rec.category}</span>
                  </div>
                  <p className="text-xs font-semibold text-slate-300">{rec.title}</p>
                  <p className="text-[11px] text-slate-500 leading-relaxed">{rec.description}</p>
                  <p className="text-[10px] text-emerald-500/80 italic">Expected: {rec.expected_impact}</p>
                </div>
              ))}
            </div>
          )}

          {/* ── Health Insights ── */}
          {result.explanation?.length > 0 && (
            <div className="glass-card p-5 space-y-3">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>💡</span> Health Insights
              </h3>
              {result.explanation.map((text, i) => (
                <p key={i} className="text-xs text-slate-400 leading-relaxed pl-4 border-l-2 border-brand-500/30">
                  {text}
                </p>
              ))}
            </div>
          )}

          {/* ── Structured AI Summary (NEW — renders JSON as cards) ── */}
          {result.ai_summary && typeof result.ai_summary === 'object' && (
            <div className="glass-card p-5 space-y-4 border border-brand-500/15">
              <h3 className="text-xs font-semibold text-brand-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>🤖</span> AI Health Analysis
              </h3>

              {/* Summary */}
              <p className="text-xs text-slate-300 leading-relaxed italic bg-white/[0.02] rounded-lg p-3">
                "{result.ai_summary.summary}"
              </p>

              {/* Risk Level + Confidence */}
              <div className="flex items-center gap-3">
                <span className={`text-xs font-bold px-3 py-1 rounded-full ${
                  result.ai_summary.risk_level === 'High' ? 'bg-rose-500/20 text-rose-400' :
                  result.ai_summary.risk_level === 'Medium' ? 'bg-amber-500/20 text-amber-400' :
                  'bg-emerald-500/20 text-emerald-400'
                }`}>
                  Risk: {result.ai_summary.risk_level}
                </span>
                <span className="text-xs text-slate-400">
                  Confidence: <span className="font-bold text-white">{result.ai_summary.confidence}</span>
                </span>
              </div>

              {/* Key Factors */}
              {result.ai_summary.key_factors?.length > 0 && (
                <div>
                  <p className="text-[10px] text-slate-500 uppercase mb-1.5 font-medium">Key Factors</p>
                  <div className="flex flex-wrap gap-1.5">
                    {result.ai_summary.key_factors.map((f, i) => (
                      <span key={i} className="text-[10px] px-2.5 py-1 rounded-full bg-brand-500/10 text-brand-300 border border-brand-500/15">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {result.ai_summary.recommendations?.length > 0 && (
                <div>
                  <p className="text-[10px] text-slate-500 uppercase mb-1.5 font-medium">AI Recommendations</p>
                  <div className="space-y-1.5">
                    {result.ai_summary.recommendations.map((r, i) => (
                      <div key={i} className="flex items-start gap-2 text-xs text-slate-300">
                        <span className="text-brand-400 font-bold mt-0.5 flex-shrink-0">{i + 1}.</span>
                        <span className="leading-relaxed">{r}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Fallback: AI Summary as string (backward compat) ── */}
          {result.ai_summary && typeof result.ai_summary === 'string' && (
            <div className="glass-card p-5 space-y-3 border border-brand-500/10">
              <h3 className="text-xs font-semibold text-brand-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>🤖</span> AI Health Advisor
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed italic">"{result.ai_summary}"</p>
            </div>
          )}

          {/* ── AI Action Plan (structured JSON) ── */}
          {result.ai_action_plan && typeof result.ai_action_plan === 'object' && (
            <div className="glass-card p-5 space-y-3 border border-brand-500/10">
              <h3 className="text-xs font-semibold text-brand-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>📋</span> AI Action Plan (Powered by Groq)
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed italic bg-white/[0.02] rounded-lg p-3">
                "{result.ai_action_plan.summary}"
              </p>
              {result.ai_action_plan.recommendations?.length > 0 && (
                <div className="space-y-1.5">
                  {result.ai_action_plan.recommendations.map((r, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-slate-300">
                      <span className="text-emerald-400 font-bold mt-0.5 flex-shrink-0">✓</span>
                      <span className="leading-relaxed">{r}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── Fallback: AI Action Plan as string ── */}
          {result.ai_action_plan && typeof result.ai_action_plan === 'string' && (
            <div className="glass-card p-5 space-y-3 border border-brand-500/10">
              <h3 className="text-xs font-semibold text-brand-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>📋</span> AI Action Plan
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">{result.ai_action_plan}</p>
            </div>
          )}

          {/* ── Model Trust ── */}
          {result.model_info && (
            <div className="glass-card p-4 space-y-1">
              <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                🔬 Model Transparency
              </h3>
              <div className="grid grid-cols-4 gap-3 text-center">
                <div>
                  <p className="text-[10px] font-bold text-white">{result.model_info.type || 'Ensemble'}</p>
                  <p className="text-[9px] text-slate-600">Model Type</p>
                </div>
                <div>
                  <p className="text-xs font-bold text-white">{result.model_info.dataset}</p>
                  <p className="text-[9px] text-slate-600">Training Data</p>
                </div>
                <div>
                  <p className="text-xs font-bold text-white">
                    {typeof result.model_info.accuracy_r2 === 'number'
                      ? (result.model_info.accuracy_r2 * 100).toFixed(1) + '%'
                      : result.model_info.accuracy_r2}
                  </p>
                  <p className="text-[9px] text-slate-600">Model R²</p>
                </div>
                <div>
                  <p className="text-xs font-bold text-white">
                    {typeof result.model_info.disease_accuracy === 'number'
                      ? (result.model_info.disease_accuracy * 100).toFixed(1) + '%'
                      : result.model_info.disease_accuracy}
                  </p>
                  <p className="text-[9px] text-slate-600">Disease Acc.</p>
                </div>
              </div>
            </div>
          )}

          {/* ── Disclaimer ── */}
          {result.disclaimer && (
            <p className="text-[10px] text-slate-600 text-center italic px-4 leading-relaxed">
              ⚕️ {result.disclaimer}
            </p>
          )}

          {/* ── Time-Series Chart ── */}
          {result.future_vitals?.length > 0 && (
            <SimulationChart
              futureVitals={result.future_vitals}
              baselineVitals={result.baseline_vitals}
            />
          )}
        </div>
      )}
    </div>
  );
}


/* ─── Slider ─── */
function Slider({ id, label, value, min, max, step = 1, unit, onChange, color, icon }) {
  const colorMap = {
    emerald: 'accent-emerald-500', indigo: 'accent-indigo-500', amber: 'accent-amber-500',
  };
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label htmlFor={id} className="text-sm text-slate-300 flex items-center gap-1.5">
          <span>{icon}</span> {label}
        </label>
        <span className="text-sm font-bold text-white tabular-nums">
          {value}<span className="text-xs text-slate-500 font-normal ml-1">{unit}</span>
        </span>
      </div>
      <input id={id} type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className={`w-full h-1.5 rounded-full appearance-none cursor-pointer bg-white/10 ${colorMap[color] || 'accent-brand-500'}
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
          [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:shadow-md
          [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:transition-transform [&::-webkit-slider-thumb]:hover:scale-125`}
      />
      <div className="flex justify-between text-[10px] text-slate-600"><span>{min}</span><span>{max}</span></div>
    </div>
  );
}

/* ─── NumberInput ─── */
function NumberInput({ label, value, min, max, unit, onChange }) {
  return (
    <div className="space-y-1">
      <label className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">{label}</label>
      <div className="flex items-center gap-1">
        <input type="number" value={value} min={min} max={max}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-sm text-white
            focus:outline-none focus:border-brand-500/50 focus:ring-1 focus:ring-brand-500/20
            [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
        />
        <span className="text-[10px] text-slate-600 whitespace-nowrap">{unit}</span>
      </div>
    </div>
  );
}

/* ─── RiskCard ─── */
function RiskCard({ label, score, level, confidence }) {
  const getColor = (s) => s >= 75 ? 'rose' : s >= 55 ? 'orange' : s >= 35 ? 'amber' : 'emerald';
  const color = score != null ? getColor(score) : 'slate';

  const colorClasses = {
    rose: 'bg-rose-500/20 text-rose-400',
    orange: 'bg-orange-500/20 text-orange-400',
    amber: 'bg-amber-500/20 text-amber-400',
    emerald: 'bg-emerald-500/20 text-emerald-400',
    slate: 'bg-white/10 text-slate-400',
  };

  return (
    <div className="bg-white/5 rounded-xl p-3 text-center space-y-1">
      <p className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold">{score?.toFixed(1) ?? '—'}</p>
      {level && (
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${colorClasses[color]}`}>
          {level}
        </span>
      )}
      {confidence != null && (
        <p className="text-[10px] text-slate-600">{(confidence * 100).toFixed(0)}% confidence</p>
      )}
    </div>
  );
}

/* ─── HealthScoreCard ─── */
function HealthScoreCard({ label, data }) {
  const gradeColorClasses = {
    A: 'bg-emerald-500/20 text-emerald-400',
    B: 'bg-blue-500/20 text-blue-400',
    C: 'bg-amber-500/20 text-amber-400',
    D: 'bg-orange-500/20 text-orange-400',
    F: 'bg-rose-500/20 text-rose-400',
  };
  const colorClass = gradeColorClasses[data.grade] || 'bg-white/10 text-slate-400';

  return (
    <div className="bg-white/5 rounded-xl p-3 text-center space-y-1">
      <p className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold">{data.health_score.toFixed(0)}</p>
      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${colorClass}`}>
        Grade {data.grade}
      </span>
      <p className="text-[10px] text-slate-600 capitalize">
        Best: {data.strongest_area?.replace(/_/g, ' ')}
      </p>
    </div>
  );
}
