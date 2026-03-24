/**
 * App — Main dashboard layout.
 * Composes MetricsPanel, AgentBrain, ScalingTimeline, TrainingStats, ArchitectureDiagram.
 */
import React from 'react';
import { useFirebase } from './hooks/useFirebase.js';
import MetricsPanel from './components/MetricsPanel.jsx';
import AgentBrain from './components/AgentBrain.jsx';
import ScalingTimeline from './components/ScalingTimeline.jsx';
import TrainingStats from './components/TrainingStats.jsx';
import ArchitectureDiagram from './components/ArchitectureDiagram.jsx';

export default function App() {
  const {
    decisions, metrics, actionProbs, isOnline, agentStatus,
    trainingStats, currentEpisode, totalEpisodes, source,
  } = useFirebase();

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header__badge">
          <span className="header__badge-dot" />
          {source === 'firebase' ? 'Live from Firebase' :
           source === 'demo-api' ? 'Connected to Agent' : 'Simulation Mode'}
        </div>
        <h1 className="header__title">RL Autoscaler</h1>
        <p className="header__subtitle">
          Intelligent Predictive Autoscaling powered by Reinforcement Learning
        </p>
      </header>

      {/* Live Metrics Gauges */}
      <MetricsPanel metrics={metrics} />

      {/* Training + Agent Brain row */}
      <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 1fr', marginTop: '1.5rem' }}>
        <TrainingStats
          trainingStats={trainingStats}
          currentEpisode={currentEpisode}
          totalEpisodes={totalEpisodes}
          agentStatus={agentStatus}
        />
        <AgentBrain actionProbs={actionProbs} />
      </div>

      {/* Timeline + Architecture row */}
      <div className="dashboard-grid" style={{ gridTemplateColumns: '1.5fr 1fr', marginTop: '1.5rem' }}>
        <ScalingTimeline decisions={decisions} />
        <ArchitectureDiagram />
      </div>

      {/* Footer */}
      <footer className="footer">
        <div className={`status-indicator ${isOnline ? 'status-indicator--healthy' : 'status-indicator--offline'}`}>
          <span className="status-indicator__dot" />
          Agent: {agentStatus} | Source: {source}
        </div>
        <p style={{ marginTop: '0.5rem' }}>
          Intelligent Predictive Autoscaler — Hybrid AWS + GCP + Firebase
        </p>
      </footer>
    </div>
  );
}
