/**
 * ScalingTimeline — Animated timeline of recent scaling decisions.
 */
import React from 'react';

function formatTime(timestamp) {
  const d = new Date(timestamp * 1000);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function getBadgeClass(action) {
  switch (action) {
    case 'SCALE_UP': return 'badge--scale-up';
    case 'SCALE_DOWN': return 'badge--scale-down';
    default: return 'badge--maintain';
  }
}

export default function ScalingTimeline({ decisions = [] }) {
  return (
    <div className="glass-card">
      <div className="card-title">
        <span>📈</span>
        Scaling Timeline
      </div>
      <div className="timeline">
        {decisions.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
            Waiting for scaling decisions...
          </div>
        )}
        {decisions.slice(0, 30).map((d, i) => (
          <div
            key={d.id || i}
            className="timeline-item"
            style={{ animationDelay: `${i * 0.03}s` }}
          >
            <span className={`timeline-item__badge ${getBadgeClass(d.action)}`}>
              {d.action === 'SCALE_UP' ? '▲ UP' : d.action === 'SCALE_DOWN' ? '▼ DOWN' : '● HOLD'}
            </span>
            <span className="timeline-item__detail">
              {d.previous_replicas} → {d.new_replicas} replicas
              <span style={{ margin: '0 0.5rem', opacity: 0.3 }}>|</span>
              CPU {(d.cpu_utilization * 100).toFixed(0)}%
              <span style={{ margin: '0 0.5rem', opacity: 0.3 }}>|</span>
              {formatTime(d.timestamp)}
            </span>
            <span
              className="timeline-item__confidence"
              style={{
                color: d.confidence_score > 0.8
                  ? 'var(--accent-emerald)'
                  : d.confidence_score > 0.5
                    ? 'var(--accent-amber)'
                    : 'var(--accent-rose)',
              }}
            >
              {(d.confidence_score * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
