import React, { useEffect, useState } from 'react';
import { RefreshCw, Inbox, Filter } from 'lucide-react';
import api from '../api';
import ExceptionCard from '../components/ExceptionCard';

export default function IncomingIssues() {
  const [exceptions, setExceptions] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api.getExceptions({ limit: 50 }).then(d => {
      if (Array.isArray(d)) setExceptions(d);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const filtered = filter === 'all' ? exceptions
    : exceptions.filter(e => e.status === filter);

  const statusCounts = {};
  exceptions.forEach(e => {
    const s = e.status || 'unknown';
    statusCounts[s] = (statusCounts[s] || 0) + 1;
  });

  return (
    <div className="page fade-in">
      {/* ── Page Header ── */}
      <div className="page-header">
        <div>
          <h1>Incoming Issues</h1>
          <p className="page-subtitle">Browse and filter all exception cases from Celonis</p>
        </div>
        <button className="btn-primary" onClick={() => {
          api.processAll().then(() => load());
        }}><RefreshCw size={14} /> Refresh from Celonis</button>
      </div>

      {/* ── Summary Stats Bar ── */}
      <div className="stat-row">
        <div className="inline-stat">
          <span className="inline-stat-value">{exceptions.length}</span>
          <span className="inline-stat-label">Total</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value">{statusCounts['new'] || 0}</span>
          <span className="inline-stat-label">New</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value">{statusCounts['pending_decision'] || 0}</span>
          <span className="inline-stat-label">Pending</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value">{statusCounts['completed'] || 0}</span>
          <span className="inline-stat-label">Completed</span>
        </div>
      </div>

      {/* ── Action Bar: Filters ── */}
      <div className="action-bar">
        <div className="action-bar-left">
          <Filter size={14} style={{ color: 'var(--text-muted)' }} />
          {['all', 'new', 'pending_decision', 'approved', 'completed', 'rejected'].map(s => (
            <button key={s} onClick={() => setFilter(s)}
              className={`filter-btn${filter === s ? ' active' : ''}`}>
              {s === 'all' ? 'All' : s.replace(/_/g, ' ')}
              <span className="filter-count">
                {s === 'all' ? exceptions.length : (statusCounts[s] || 0)}
              </span>
            </button>
          ))}
        </div>
        <div className="action-bar-right">
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Showing {filtered.length} of {exceptions.length}
          </span>
        </div>
      </div>

      {/* ── Content ── */}
      {loading ? (
        <div className="loading">Loading exceptions...</div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon"><Inbox size={20} /></div>
          <div className="empty-state-title">No exceptions found</div>
          <div className="empty-state-desc">
            {filter !== 'all'
              ? `No exceptions with status "${filter.replace(/_/g, ' ')}". Try a different filter.`
              : 'Run python main.py to process sample data.'}
          </div>
        </div>
      ) : (
        <div className="card-grid">
          {filtered.map(exc => <ExceptionCard key={exc.id} exc={exc} />)}
        </div>
      )}
    </div>
  );
}