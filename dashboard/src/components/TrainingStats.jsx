/**
 * TrainingStats — Displays training progress: episodes, reward, losses.
 */
import React from 'react';

export default function TrainingStats({
  trainingStats = {},
  currentEpisode = 0,
  totalEpisodes = 0,
  agentStatus = 'unknown',
}) {
  const { best_reward = 0, current_reward = 0, policy_loss = 0, value_loss = 0 } = trainingStats;
  const progress = totalEpisodes > 0 ? (currentEpisode / totalEpisodes) * 100 : 0;

  const statusColor =
    agentStatus === 'trained' ? 'var(--accent-emerald)' :
    agentStatus === 'training' ? 'var(--accent-amber)' :
    'var(--text-muted)';

  return (
    <div className="glass-card">
      <div className="card-title">
        <span>📊</span>
        Training Progress
      </div>

      {/* Status Badge */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.5rem',
        marginBottom: '1.25rem',
      }}>
        <span style={{
          display: 'inline-block', width: 10, height: 10,
          borderRadius: '50%', background: statusColor,
          boxShadow: `0 0 8px ${statusColor}`,
          animation: agentStatus === 'training' ? 'pulse-dot 1.5s ease-in-out infinite' : 'none',
        }} />
        <span style={{
          fontSize: '0.85rem', fontWeight: 600,
          textTransform: 'uppercase', letterSpacing: '0.08em',
          color: statusColor,
        }}>
          {agentStatus}
        </span>
        {totalEpisodes > 0 && (
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
            Episode {currentEpisode} / {totalEpisodes}
          </span>
        )}
      </div>

      {/* Progress Bar */}
      {totalEpisodes > 0 && (
        <div style={{ marginBottom: '1.25rem' }}>
          <div className="gauge__bar">
            <div
              className="gauge__fill gauge__fill--indigo"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr',
        gap: '1rem',
      }}>
        <div className="metric">
          <span className="metric__value metric__value--emerald" style={{ fontSize: '1.4rem' }}>
            {best_reward}
          </span>
          <span className="metric__label">Best Reward</span>
        </div>
        <div className="metric">
          <span className="metric__value metric__value--cyan" style={{ fontSize: '1.4rem' }}>
            {current_reward}
          </span>
          <span className="metric__label">Current Reward</span>
        </div>
        <div className="metric">
          <span className="metric__value metric__value--rose" style={{ fontSize: '1.4rem' }}>
            {policy_loss}
          </span>
          <span className="metric__label">Policy Loss</span>
        </div>
        <div className="metric">
          <span className="metric__value metric__value--amber" style={{ fontSize: '1.4rem' }}>
            {value_loss}
          </span>
          <span className="metric__label">Value Loss</span>
        </div>
      </div>
    </div>
  );
}
