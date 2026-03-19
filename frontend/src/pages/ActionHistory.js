import React, { useEffect, useState } from 'react';
import { Zap } from 'lucide-react';
import api from '../api';

const COLORS = {
  completed: '#34d399', failed: '#f87171',
  pending: '#fbbf24', executing: '#60a5fa', rolled_back: '#6b7280',
};

export default function ActionHistory() {
  const [actions, setActions] = useState([]);

  useEffect(() => {
    api.getActions().then(d => { if (Array.isArray(d)) setActions(d); }).catch(() => { });
  }, []);

  // Compute status counts
  const statusCounts = {};
  actions.forEach(a => {
    const s = a.status || 'unknown';
    statusCounts[s] = (statusCounts[s] || 0) + 1;
  });

  return (
    <div className="page fade-in">
      {/* ── Header ── */}
      <div className="page-header">
        <div>
          <h1>Action History</h1>
          <p className="page-subtitle">All actions executed — auto and human-approved</p>
        </div>
      </div>

      {/* ── Summary Stats ── */}
      <div className="stat-row">
        <div className="inline-stat">
          <span className="inline-stat-value">{actions.length}</span>
          <span className="inline-stat-label">Total</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value" style={{ color: 'var(--green)' }}>{statusCounts['completed'] || 0}</span>
          <span className="inline-stat-label">Completed</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value" style={{ color: 'var(--red)' }}>{statusCounts['failed'] || 0}</span>
          <span className="inline-stat-label">Failed</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value" style={{ color: 'var(--yellow)' }}>{statusCounts['pending'] || 0}</span>
          <span className="inline-stat-label">Pending</span>
        </div>
      </div>

      {/* ── Content ── */}
      {actions.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon"><Zap size={20} /></div>
          <div className="empty-state-title">No actions executed yet</div>
          <div className="empty-state-desc">Actions will appear here once exceptions are processed and decisions are made.</div>
        </div>
      ) : (
        <div className="section-card">
          <div className="section-card-header">
            <h3>Execution Log</h3>
            <span className="section-meta">{actions.length} actions</span>
          </div>
          <div style={{ overflow: 'auto' }}>
            <table className="data-table" style={{ borderRadius: 0, border: 'none' }}>
              <thead><tr>
                <th>Exception</th><th>Action</th><th>Status</th>
                <th>Target</th><th>By</th><th>Result</th><th>Date</th>
              </tr></thead>
              <tbody>
                {actions.map(a => (
                  <tr key={a.id}>
                    <td className="mono">{(a.exception_id || '').slice(0, 12)}...</td>
                    <td>{(a.action_type || '').replace(/_/g, ' ')}</td>
                    <td><span className="status-dot" style={{ color: COLORS[a.status] }}>{a.status}</span></td>
                    <td><span className={`target-badge target-${a.execution_target}`}>{a.execution_target}</span></td>
                    <td>{a.executed_by}</td>
                    <td>{a.result?.message || a.result?.error || '—'}</td>
                    <td>{a.created_at ? new Date(a.created_at).toLocaleDateString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}