/**
 * ArchitectureDiagram — Visual architecture overview of the multi-cloud system.
 * Pure SVG rendering, no external dependencies.
 */
import React from 'react';

const BOXES = [
  { id: 'aws', x: 40, y: 20, w: 200, h: 120, label: '☁️ AWS (EC2 + K3s)', color: '#ff9900', items: ['EC2 Instance', 'Prometheus', 'web-app pods'] },
  { id: 'agent', x: 280, y: 20, w: 200, h: 120, label: '🧠 RL Agent', color: '#8b5cf6', items: ['PPO Actor-Critic', 'Gym Environment', 'K3s Scaler'] },
  { id: 'gcp', x: 40, y: 180, w: 200, h: 110, label: '🌐 Google Cloud', color: '#4285f4', items: ['Cloud Storage', 'Vertex AI', 'Cloud Function'] },
  { id: 'firebase', x: 280, y: 180, w: 200, h: 110, label: '🔥 Firebase', color: '#ffca28', items: ['Realtime DB', 'Hosting', 'Dashboard'] },
];

const CONNECTIONS = [
  { from: 'aws', to: 'agent', label: 'metrics' },
  { from: 'agent', to: 'aws', label: 'kubectl', dy: 12 },
  { from: 'agent', to: 'firebase', label: 'decisions' },
  { from: 'gcp', to: 'agent', label: 'model', dy: -8 },
  { from: 'aws', to: 'gcp', label: 'S3→GCS' },
];

export default function ArchitectureDiagram() {
  return (
    <div className="glass-card">
      <div className="card-title">
        <span>🏗️</span>
        System Architecture
      </div>
      <svg viewBox="0 0 520 310" style={{ width: '100%', height: 'auto' }}>
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
          <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#94a3b8" />
          </marker>
        </defs>

        {/* Boxes */}
        {BOXES.map(box => (
          <g key={box.id}>
            <rect x={box.x} y={box.y} width={box.w} height={box.h}
              rx="8" fill={`${box.color}15`} stroke={`${box.color}60`} strokeWidth="1.5" />
            <text x={box.x + box.w / 2} y={box.y + 18} textAnchor="middle"
              fill={box.color} fontSize="11" fontWeight="700" fontFamily="Inter, sans-serif">
              {box.label}
            </text>
            {box.items.map((item, i) => (
              <text key={i} x={box.x + box.w / 2} y={box.y + 38 + i * 18} textAnchor="middle"
                fill="#94a3b8" fontSize="9" fontFamily="JetBrains Mono, monospace">
                {item}
              </text>
            ))}
          </g>
        ))}

        {/* Connection lines */}
        {CONNECTIONS.map((conn, i) => {
          const from = BOXES.find(b => b.id === conn.from);
          const to = BOXES.find(b => b.id === conn.to);
          const fx = from.x + from.w / 2;
          const fy = from.y + from.h / 2 + (conn.dy || 0);
          const tx = to.x + to.w / 2;
          const ty = to.y + to.h / 2 + (conn.dy || 0);
          // Find edge points
          const dx = tx - fx, dy = ty - fy;
          const ax = Math.abs(dx), ay = Math.abs(dy);
          let sx, sy, ex, ey;
          if (ax > ay) {
            sx = fx + (dx > 0 ? from.w / 2 : -from.w / 2);
            sy = fy;
            ex = tx + (dx > 0 ? -to.w / 2 : to.w / 2);
            ey = ty;
          } else {
            sx = fx;
            sy = fy + (dy > 0 ? from.h / 2 : -from.h / 2);
            ex = tx;
            ey = ty + (dy > 0 ? -to.h / 2 : to.h / 2);
          }
          const mx = (sx + ex) / 2, my = (sy + ey) / 2;
          return (
            <g key={i}>
              <line x1={sx} y1={sy} x2={ex} y2={ey}
                stroke="#94a3b850" strokeWidth="1" markerEnd="url(#arrowhead)" />
              <rect x={mx - 22} y={my - 7} width="44" height="14" rx="3"
                fill="#0a0e1a" stroke="#94a3b830" strokeWidth="0.5" />
              <text x={mx} y={my + 3} textAnchor="middle"
                fill="#94a3b8" fontSize="7" fontFamily="JetBrains Mono, monospace">
                {conn.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
