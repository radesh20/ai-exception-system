import React, { useEffect, useState } from 'react';
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
    <div className="page">
      <div className="page-header">
        <h1>📥 Incoming Issues</h1>
        <button className="btn-primary" onClick={() => {
          api.processAll().then(() => load());
        }}>🔄 Refresh from Celonis</button>
      </div>

      <div className="filter-row">
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

      {loading ? (
        <div className="loading">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">No exceptions found.</div>
      ) : (
        <div className="card-grid">
          {filtered.map(exc => <ExceptionCard key={exc.id} exc={exc} />)}
        </div>
      )}
    </div>
  );
}