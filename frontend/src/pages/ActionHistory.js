import React, { useEffect, useState } from 'react';
import api from '../api';

const COLORS = {
  completed: '#198754', failed: '#dc3545',
  pending: '#ffc107', executing: '#0d6efd', rolled_back: '#6c757d',
};

export default function ActionHistory() {
  const [actions, setActions] = useState([]);

  useEffect(() => {
    api.getActions().then(d => { if (Array.isArray(d)) setActions(d); }).catch(() => {});
  }, []);

  return (
    <div className="page">
      <h1>⚡ Action History</h1>
      <p className="page-desc">All actions executed — auto and human-approved.</p>

      {actions.length === 0 ? (
        <div className="empty-state">No actions executed yet.</div>
      ) : (
        <table className="data-table">
          <thead><tr>
            <th>Exception</th><th>Action</th><th>Status</th>
            <th>Target</th><th>By</th><th>Result</th><th>Date</th>
          </tr></thead>
          <tbody>
            {actions.map(a => (
              <tr key={a.id}>
                <td className="mono">{(a.exception_id || '').slice(0, 12)}...</td>
                <td>{(a.action_type || '').replace(/_/g, ' ')}</td>
                <td><span className="status-dot" style={{color: COLORS[a.status]}}>{a.status}</span></td>
                <td><span className={`target-badge target-${a.execution_target}`}>{a.execution_target}</span></td>
                <td>{a.executed_by}</td>
                <td>{a.result?.message || a.result?.error || '—'}</td>
                <td>{a.created_at ? new Date(a.created_at).toLocaleDateString() : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}