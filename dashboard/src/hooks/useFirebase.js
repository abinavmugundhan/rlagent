/**
 * useFirebase — Connects to Firebase RTDB for live data.
 * Falls back to local demo API server, then to simulated data.
 *
 * Priority:
 *  1. Firebase RTDB (if configured via env vars)
 *  2. Local demo API at http://localhost:8888/api/state
 *  3. Self-generated simulation data
 */
import { useState, useEffect, useRef } from 'react';

const DEMO_API_URL = 'http://localhost:8888/api/state';

// ─── Simulated Data Generator ──────────────────────────────────────────────

function generateMockDecision(index) {
  const actions = ['SCALE_UP', 'SCALE_DOWN', 'MAINTAIN', 'MAINTAIN', 'MAINTAIN'];
  const action = actions[Math.floor(Math.random() * actions.length)];
  const prevReplicas = Math.floor(Math.random() * 8) + 2;
  const newReplicas =
    action === 'SCALE_UP' ? prevReplicas + 1 :
    action === 'SCALE_DOWN' ? Math.max(1, prevReplicas - 1) :
    prevReplicas;

  return {
    id: `mock-${Date.now()}-${index}`,
    action,
    previous_replicas: prevReplicas,
    new_replicas: newReplicas,
    confidence_score: 0.6 + Math.random() * 0.35,
    cpu_utilization: 0.3 + Math.random() * 0.5,
    memory_utilization: 0.25 + Math.random() * 0.45,
    request_rate: 150 + Math.random() * 800,
    timestamp: Date.now() / 1000 - index * 15,
  };
}

function generateMockMetrics() {
  const hour = new Date().getHours();
  const diurnal = 0.3 + 0.35 * Math.sin(Math.PI * (hour - 4) / 12);
  const cpu = Math.min(0.95, Math.max(0.05, diurnal + (Math.random() - 0.5) * 0.15));
  const mem = Math.min(0.95, Math.max(0.05, cpu * (0.7 + Math.random() * 0.3)));
  const rps = Math.max(10, diurnal * 1000 + (Math.random() - 0.5) * 100);
  return {
    cpu_utilization: cpu,
    memory_utilization: mem,
    request_rate: rps,
    replicas: Math.floor(Math.random() * 8) + 2,
  };
}

function generateMockActionProbs() {
  const raw = [Math.random(), Math.random(), Math.random()];
  const sum = raw.reduce((a, b) => a + b, 0);
  return raw.map(v => v / sum);
}

// ─── Hook ──────────────────────────────────────────────────────────────────

export function useFirebase() {
  const [decisions, setDecisions] = useState([]);
  const [metrics, setMetrics] = useState(generateMockMetrics());
  const [actionProbs, setActionProbs] = useState([0.2, 0.6, 0.2]);
  const [isOnline, setIsOnline] = useState(false);
  const [agentStatus, setAgentStatus] = useState('connecting...');
  const [trainingStats, setTrainingStats] = useState({
    best_reward: 0, current_reward: 0, policy_loss: 0, value_loss: 0,
  });
  const [currentEpisode, setCurrentEpisode] = useState(0);
  const [totalEpisodes, setTotalEpisodes] = useState(0);
  const sourceRef = useRef('none'); // 'firebase', 'demo-api', 'simulation'

  useEffect(() => {
    let intervalId = null;
    let stopped = false;

    // ─── Try Demo API ──────────────────────────────────────────────
    async function tryDemoAPI() {
      try {
        const res = await fetch(DEMO_API_URL);
        if (!res.ok) throw new Error('Demo API not available');
        const data = await res.json();
        applyDemoData(data);
        sourceRef.current = 'demo-api';
        setIsOnline(true);
        return true;
      } catch {
        return false;
      }
    }

    function applyDemoData(data) {
      if (data.metrics) setMetrics(data.metrics);
      if (data.action_probs) setActionProbs(data.action_probs);
      if (data.decisions) setDecisions(data.decisions);
      if (data.agent_status) setAgentStatus(data.agent_status);
      if (data.training_stats) setTrainingStats(data.training_stats);
      if (data.current_episode !== undefined) setCurrentEpisode(data.current_episode);
      if (data.total_episodes !== undefined) setTotalEpisodes(data.total_episodes);
    }

    // ─── Try Firebase ──────────────────────────────────────────────
    async function tryFirebase() {
      try {
        const apiKey = import.meta.env.VITE_FIREBASE_API_KEY || '';
        const dbUrl = import.meta.env.VITE_FIREBASE_DB_URL || '';
        if (!apiKey || !dbUrl) return false;

        const { initializeApp } = await import('firebase/app');
        const { getDatabase, ref, onValue, query, limitToLast } = await import('firebase/database');

        const app = initializeApp({
          apiKey,
          projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || '',
          databaseURL: dbUrl,
        });
        const db = getDatabase(app);

        onValue(query(ref(db, '/autoscaler/decisions'), limitToLast(50)), (snapshot) => {
          const data = snapshot.val();
          if (data) {
            const list = Object.entries(data)
              .map(([key, val]) => ({ id: key, ...val }))
              .sort((a, b) => b.timestamp - a.timestamp);
            setDecisions(list);
          }
        });

        onValue(ref(db, '/autoscaler/health'), (snapshot) => {
          const data = snapshot.val();
          if (data) {
            setAgentStatus(data.status);
            setIsOnline(true);
          }
        });

        sourceRef.current = 'firebase';
        setIsOnline(true);
        return true;
      } catch {
        return false;
      }
    }

    // ─── Fallback Simulation ───────────────────────────────────────
    function startSimulation() {
      sourceRef.current = 'simulation';
      setAgentStatus('simulated');
      const initial = Array.from({ length: 20 }, (_, i) => generateMockDecision(i));
      setDecisions(initial);

      intervalId = setInterval(() => {
        if (stopped) return;
        setMetrics(generateMockMetrics());
        setActionProbs(generateMockActionProbs());
        if (Math.random() < 0.3) {
          setDecisions(prev => [generateMockDecision(0), ...prev.slice(0, 49)]);
        }
      }, 2000);
    }

    // ─── Initialize ────────────────────────────────────────────────
    async function init() {
      // Try Firebase first
      const fbOk = await tryFirebase();
      if (fbOk) return;

      // Try demo API
      const apiOk = await tryDemoAPI();
      if (apiOk) {
        // Poll demo API
        intervalId = setInterval(async () => {
          if (stopped) return;
          try {
            const res = await fetch(DEMO_API_URL);
            if (res.ok) {
              const data = await res.json();
              applyDemoData(data);
            }
          } catch {
            // API went offline, switch to simulation
            if (sourceRef.current === 'demo-api') {
              setIsOnline(false);
              startSimulation();
            }
          }
        }, 1000);
        return;
      }

      // Fallback to simulation
      startSimulation();
    }

    init();

    return () => {
      stopped = true;
      if (intervalId) clearInterval(intervalId);
    };
  }, []);

  return {
    decisions,
    metrics,
    actionProbs,
    isOnline,
    agentStatus,
    trainingStats,
    currentEpisode,
    totalEpisodes,
    source: sourceRef.current,
  };
}
