import { useState, useEffect, useRef, useCallback } from 'react';
import Dashboard from './components/Dashboard';
import Chart from './components/Chart';
import AdvancedSimulation from './components/AdvancedSimulation';

const API_BASE = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/vitals';

export default function App() {
  // ─── State ───
  const [vitals, setVitals] = useState(null);
  const [history, setHistory] = useState([]);
  const [riskScore, setRiskScore] = useState(0);
  const [healthScore, setHealthScore] = useState(0);
  const [healthGrade, setHealthGrade] = useState(null);
  const [connected, setConnected] = useState(false);
  const [diseaseClassification, setDiseaseClassification] = useState(null);
  const [diseaseConfidence, setDiseaseConfidence] = useState(null);
  const [stabilityStatus, setStabilityStatus] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [hsProgression, setHsProgression] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  // ─── Demo Spike/Dip ───
  const triggerSpike = async (direction) => {
    try {
      await fetch(`${API_BASE}/demo-spike`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction }),
      });
    } catch (err) {
      console.error('Spike trigger error:', err);
    }
  };

  // ─── WebSocket connection with auto-reconnect ───
  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('🟢 WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        setVitals(data);
        setRiskScore(data.risk_score ?? 0);
        setHealthScore(data.health_score ?? 0);
        setHealthGrade(data.health_grade ?? null);
        setDiseaseClassification(data.disease_classification ?? null);
        setDiseaseConfidence(data.disease_confidence ?? null);
        setStabilityStatus(data.stability_status ?? null);
        setTrendData(data.trend_data ?? null);
        setHsProgression(data.hs_progression ?? null);
        setHistory((prev) => {
          const next = [...prev, data];
          return next.length > 30 ? next.slice(-30) : next;
        });
      } catch (err) {
        console.error('WS parse error:', err);
      }
    };

    ws.onclose = () => {
      console.log('🔴 WebSocket disconnected — reconnecting in 3s…');
      setConnected(false);
      reconnectTimer.current = setTimeout(connectWs, 3000);
    };

    ws.onerror = () => ws.close();

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/vitals/history`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setHistory(data);
      })
      .catch(() => {});

    connectWs();

    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connectWs]);

  // ─── Render ───
  return (
    <div className="min-h-screen px-4 py-8 md:px-8 lg:px-16 max-w-[1440px] mx-auto">
      {/* Header */}
      <header className="mb-10 animate-fade-in">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-3 h-3 rounded-full bg-brand-400 animate-pulse-slow" />
          <span className="text-xs font-medium uppercase tracking-widest text-brand-300">
            Live Patient Monitor
          </span>
          <span
            className={`ml-auto text-xs font-medium px-3 py-1 rounded-full ${
              connected
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'bg-red-500/20 text-red-400'
            }`}
          >
            {connected ? '● Connected' : '○ Reconnecting…'}
          </span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-white via-brand-200 to-brand-400 bg-clip-text text-transparent">
          Digital Twin — Patient Dashboard
        </h1>
        <p className="mt-2 text-sm text-slate-400 max-w-xl">
          AI-powered clinical decision support — real-time vitals, risk prediction,
          disease classification, and personalized&nbsp;recommendations.
        </p>

        {/* Demo Spike/Dip Buttons */}
        <div className="flex items-center gap-3 mt-4">
          <span className="text-xs text-slate-500 uppercase tracking-wider font-medium">Demo Controls:</span>
          <button
            onClick={() => triggerSpike('up')}
            className="px-4 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200
              bg-rose-500/15 text-rose-400 border border-rose-500/20
              hover:bg-rose-500/25 hover:border-rose-500/40 active:scale-95"
            title="Simulate a post-meal glucose surge and stress HR spike"
          >
            ↑ Spike Up
          </button>
          <button
            onClick={() => triggerSpike('down')}
            className="px-4 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200
              bg-emerald-500/15 text-emerald-400 border border-emerald-500/20
              hover:bg-emerald-500/25 hover:border-emerald-500/40 active:scale-95"
            title="Simulate a post-exercise recovery dip"
          >
            ↓ Dip Down
          </button>
          {stabilityStatus && (
            <span className={`ml-auto text-xs font-semibold px-3 py-1 rounded-full ${
              stabilityStatus === 'stable' ? 'bg-emerald-500/15 text-emerald-400' :
              stabilityStatus === 'moderate' ? 'bg-amber-500/15 text-amber-400' :
              'bg-rose-500/15 text-rose-400'
            }`}>
              {stabilityStatus === 'stable' ? '✓ Stable' :
               stabilityStatus === 'moderate' ? '~ Moderate' : '⚠ Volatile'}
            </span>
          )}
        </div>
      </header>

      {/* Vitals Cards */}
      <section className="mb-8 animate-slide-up">
        <Dashboard
          vitals={vitals}
          riskScore={riskScore}
          healthScore={healthScore}
          healthGrade={healthGrade}
          diseaseClassification={diseaseClassification}
          diseaseConfidence={diseaseConfidence}
          trendData={trendData}
          hsProgression={hsProgression}
        />
      </section>

      {/* Chart + Advanced Simulation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-slide-up">
        <div className="lg:col-span-2">
          <Chart history={history} />
        </div>
        <div>
          <AdvancedSimulation currentRisk={riskScore} />
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-12 text-center text-xs text-slate-600">
        Digital Twin v4.0 · Clinical Decision Support System · Ensemble ML (RF + GBR) · {new Date().getFullYear()}
      </footer>
    </div>
  );
}
