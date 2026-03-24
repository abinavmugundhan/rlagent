/**
 * App — Main dashboard layout.
 * Composes MetricsPanel, AgentBrain, and ScalingTimeline.
 */
import React from 'react';
import { useFirebase } from './hooks/useFirebase.js';
import MetricsPanel from './components/MetricsPanel.jsx';
import AgentBrain from './components/AgentBrain.jsx';
import ScalingTimeline from './components/ScalingTimeline.jsx';

export default function App() {
  const { decisions, metrics, actionProbs, isOnline, agentStatus } = useFirebase();

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header__badge">
          <span className="header__badge-dot" />
          {isOnline ? 'Live from Firebase' : 'Simulation Mode'}
        </div>
        <h1 className="header__title">RL Autoscaler</h1>
        <p className="header__subtitle">
          Intelligent Predictive Autoscaling powered by Reinforcement Learning
        </p>
      </header>

      {/* Live Metrics Gauges */}
      <MetricsPanel metrics={metrics} />

      {/* Agent Brain + Timeline side by side */}
      <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 1.5fr', marginTop: '1.5rem' }}>
        <AgentBrain actionProbs={actionProbs} />
        <ScalingTimeline decisions={decisions} />
      </div>

      {/* Footer */}
      <footer className="footer">
        <div className="status-indicator status-indicator--healthy">
          <span className="status-indicator__dot" />
          Agent Status: {agentStatus}
        </div>
        <p style={{ marginTop: '0.5rem' }}>
          Intelligent Predictive Autoscaler — Hybrid AWS + GCP
        </p>
      </footer>
    </div>
  );
}
