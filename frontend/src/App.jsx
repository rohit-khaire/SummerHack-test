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
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

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
    // Fetch initial history
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
          patient segmentation, and personalized&nbsp;recommendations.
        </p>
      </header>

      {/* Vitals Cards */}
      <section className="mb-8 animate-slide-up">
        <Dashboard vitals={vitals} riskScore={riskScore} healthScore={healthScore} healthGrade={healthGrade} />
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
        Digital Twin v3.0 · Clinical Decision Support System · PIMA-Grounded ML · {new Date().getFullYear()}
      </footer>
    </div>
  );
}
