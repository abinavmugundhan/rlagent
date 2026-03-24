/**
 * MetricsPanel — Live CPU / Memory / RPS gauges.
 */
import React from 'react';

function Gauge({ label, value, maxLabel, colorClass, icon }) {
  const pct = Math.min(value * 100, 100);
  const isHigh = value > 0.8;
  const effectiveColor = isHigh ? 'gauge__fill--rose' : colorClass;

  return (
    <div className="glass-card">
      <div className="card-title">
        <span>{icon}</span>
        {label}
      </div>
      <div className="metric">
        <span className={`metric__value ${isHigh ? 'metric__value--rose' : ''}`}>
          {pct.toFixed(1)}
          <span style={{ fontSize: '1rem', opacity: 0.6 }}>%</span>
        </span>
        <span className="metric__label">{maxLabel}</span>
      </div>
      <div className="gauge">
        <div className="gauge__bar">
          <div
            className={`gauge__fill ${effectiveColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default function MetricsPanel({ metrics }) {
  const { cpu_utilization = 0, memory_utilization = 0, request_rate = 0, replicas = 3 } = metrics;

  return (
    <div className="dashboard-grid">
      <Gauge
        label="CPU Utilization"
        value={cpu_utilization}
        maxLabel="Target: 65%"
        colorClass="gauge__fill--indigo"
        icon="⚡"
      />
      <Gauge
        label="Memory Utilization"
        value={memory_utilization}
        maxLabel="Target: 70%"
        colorClass="gauge__fill--cyan"
        icon="🧠"
      />
      <div className="glass-card">
        <div className="card-title">
          <span>📊</span>
          Request Rate
        </div>
        <div className="metric">
          <span className="metric__value metric__value--amber">
            {request_rate.toFixed(0)}
            <span style={{ fontSize: '0.9rem', opacity: 0.6 }}> rps</span>
          </span>
          <span className="metric__label">Requests per second</span>
        </div>
        <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="metric">
            <span className="metric__value metric__value--emerald" style={{ fontSize: '1.5rem' }}>
              {replicas}
            </span>
            <span className="metric__label">Active Replicas</span>
          </div>
        </div>
      </div>
    </div>
  );
}
