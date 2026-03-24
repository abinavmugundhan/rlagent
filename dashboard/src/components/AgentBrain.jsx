/**
 * AgentBrain — Visualizes the RL agent's policy output distribution.
 * Shows probability bars for each action: Scale Down, Maintain, Scale Up.
 */
import React from 'react';

const ACTION_LABELS = ['Scale Down', 'Maintain', 'Scale Up'];
const ACTION_COLORS = ['var(--accent-rose)', 'var(--accent-indigo)', 'var(--accent-emerald)'];
const ACTION_BG = [
  'rgba(251, 113, 133, 0.15)',
  'rgba(129, 140, 248, 0.15)',
  'rgba(52, 211, 153, 0.15)',
];

export default function AgentBrain({ actionProbs = [0.2, 0.6, 0.2] }) {
  const maxIdx = actionProbs.indexOf(Math.max(...actionProbs));

  return (
    <div className="glass-card">
      <div className="card-title">
        <span>🤖</span>
        Agent Brain — Policy Output
      </div>
      <div className="brain-viz">
        <div className="brain-viz__actions">
          {ACTION_LABELS.map((label, i) => (
            <div
              key={label}
              className={`brain-viz__action ${i === maxIdx ? 'brain-viz__action--active' : ''}`}
              style={i === maxIdx ? { borderColor: ACTION_COLORS[i], boxShadow: `0 0 20px ${ACTION_COLORS[i]}33` } : {}}
            >
              <div className="brain-viz__action-label">{label}</div>
              <div
                className="brain-viz__action-prob"
                style={{ color: ACTION_COLORS[i] }}
              >
                {(actionProbs[i] * 100).toFixed(1)}%
              </div>
              <div className="brain-viz__action-bar">
                <div
                  className="brain-viz__action-bar-fill"
                  style={{
                    width: `${actionProbs[i] * 100}%`,
                    background: `linear-gradient(90deg, ${ACTION_COLORS[i]}, ${ACTION_COLORS[i]}88)`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Confidence Indicator */}
        <div style={{
          display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem',
          fontSize: '0.8rem', color: 'var(--text-secondary)',
        }}>
          <span>Decision Confidence:</span>
          <span style={{
            fontFamily: 'var(--font-mono)', fontWeight: 700,
            color: actionProbs[maxIdx] > 0.7 ? 'var(--accent-emerald)' : 'var(--accent-amber)',
          }}>
            {actionProbs[maxIdx] > 0.7 ? 'HIGH' : actionProbs[maxIdx] > 0.4 ? 'MEDIUM' : 'LOW'}
          </span>
        </div>
      </div>
    </div>
  );
}
