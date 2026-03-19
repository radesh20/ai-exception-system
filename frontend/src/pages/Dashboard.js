import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Hash, Clock, CheckCircle, TrendingUp, Users, Zap, RefreshCw, AlertTriangle, ArrowRight, Inbox, ShieldCheck, Sparkles } from 'lucide-react';
import api from '../api';
import ExceptionCard from '../components/ExceptionCard';

export default function Dashboard({ config }) {
  const [stats, setStats] = useState(null);
  const [pending, setPending] = useState([]);
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    api.getStats().then(s => { if (s) setStats(s); }).catch(() => { });
    api.getPending().then(d => { if (Array.isArray(d)) setPending(d); }).catch(() => { });
    api.getExceptions({ limit: 6 }).then(d => { if (Array.isArray(d)) setRecent(d); }).catch(() => { });
  }, []);

  const handleProcessAll = () => {
    api.processAll().then(() => {
      api.getStats().then(setStats);
      api.getExceptions({ limit: 6 }).then(setRecent);
      api.getPending().then(setPending);
    });
  };

  // derive novel exceptions count from recent
  const novelCount = recent.filter(e => e.classification?.is_novel).length;

  // derive auto-resolved count
  const autoResolved = stats
    ? (stats.completed || 0) - (stats.total_decisions || 0) + (stats.total_actions || 0)
    : 0;

  // avg confidence from recent
  const avgConf = recent.length > 0
    ? (recent.reduce((sum, e) => sum + (e.classification?.confidence || 0), 0) / recent.length * 100).toFixed(0)
    : 0;

  return (
    <div className="page fade-in">

      {/* ── Page Header ── */}
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="page-subtitle">Overview of exception processing and system status</p>
        </div>
        <button className="btn-secondary" onClick={handleProcessAll}>
          <RefreshCw size={14} /> Process All Open
        </button>
      </div>

      {/* ── System Status ── */}
      {config && (
        <div className="config-status">
          <span className="config-status-label">System</span>
          <span className={`pill ${config.azure_enabled ? 'pill-green' : 'pill-gray'}`}>
            {config.azure_enabled ? 'Deep Agent' : 'Rule-Based'}
          </span>
          <span className={`pill ${config.teams_enabled ? 'pill-green' : 'pill-gray'}`}>
            Teams: {config.teams_enabled ? 'On' : 'Off'}
          </span>
          <span className={`pill ${config.outlook_enabled ? 'pill-green' : 'pill-gray'}`}>
            Outlook: {config.outlook_enabled ? 'On' : 'Off'}
          </span>
          <span className={`pill ${config.slack_enabled ? 'pill-green' : 'pill-gray'}`}>
            Slack: {config.slack_enabled ? 'On' : 'Off'}
          </span>
          <span className={`pill ${config.gmail_enabled ? 'pill-green' : 'pill-gray'}`}>
            Gmail: {config.gmail_enabled ? 'On' : 'Off'}
          </span>
          <span className="pill pill-blue">{config.storage_backend?.toUpperCase()}</span>
          <span className={`pill ${config.servicenow_enabled ? 'pill-green' : 'pill-gray'}`}>
            ServiceNow: {config.servicenow_enabled ? 'On' : 'Off'}
          </span>
        </div>
      )}

      {/* ── KPI Section ── */}
      <div className="section">
        <div className="kpi-grid">
          <KPI icon={<Hash size={20} />} label="Total Exceptions" value={stats?.total_exceptions || 0} />
          <KPI icon={<Clock size={20} />} label="Pending Review" value={stats?.pending_review || 0} alert={stats?.pending_review > 0} />
          <KPI icon={<CheckCircle size={20} />} label="Completed" value={stats?.completed || 0} />
          <KPI icon={<TrendingUp size={20} />} label="Approval Rate" value={`${((stats?.approval_rate || 0) * 100).toFixed(0)}%`} />
          <KPI icon={<Users size={20} />} label="Total Decisions" value={stats?.total_decisions || 0} />
          <KPI icon={<Zap size={20} />} label="Actions Executed" value={stats?.total_actions || 0} />
          <KPI icon={<ShieldCheck size={20} />} label="Auto-Resolved" value={autoResolved >= 0 ? autoResolved : 0} />
          <KPI icon={<TrendingUp size={20} />} label="Avg Confidence" value={`${avgConf}%`} />
        </div>
      </div>

      {/* ── Alert Banner: Pending Review ── */}
      {pending.length > 0 && (
        <div className="alert-banner">
          <AlertTriangle size={16} />
          <span>
            <strong>{pending.length}</strong> exception{pending.length > 1 ? 's' : ''} need human review.
          </span>
          <Link to="/decisions">Review Now <ArrowRight size={13} /></Link>
        </div>
      )}

      {/* ── Alert Banner: Novel Exceptions ── */}
      {novelCount > 0 && (
        <div className="alert-banner" style={{ background: 'var(--purple-bg)', borderColor: 'rgba(139,114,224,0.25)', color: 'var(--purple-text)' }}>
          <Sparkles size={16} />
          <span>
            <strong>{novelCount}</strong> novel exception{novelCount > 1 ? 's' : ''} detected — unseen patterns found.
          </span>
          <Link to="/classifier" style={{ color: 'var(--purple)', fontWeight: 600 }}>
            Review Classifier <ArrowRight size={13} />
          </Link>
        </div>
      )}

      {/* ── Main Content: Two-Column Layout ── */}
      <div className="dashboard-two-col">

        {/* Left: Recent Exceptions */}
        <div className="section-card">
          <div className="section-card-header">
            <h3>Recent Exceptions</h3>
            <span className="section-meta">{recent.length} shown</span>
          </div>
          <div className="section-card-body">
            {recent.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {recent.slice(0, 3).map(exc => (
                  <ExceptionCard key={exc.id} exc={exc} compact />
                ))}
              </div>
            ) : (
              <div className="empty-state" style={{ border: 'none', padding: '32px 16px' }}>
                <div className="empty-state-icon"><Inbox size={20} /></div>
                <div className="empty-state-title">No exceptions yet</div>
                <div className="empty-state-desc">Run <code>python main.py</code> to process sample data</div>
              </div>
            )}
          </div>
          {recent.length > 0 && (
            <div className="section-card-footer">
              <Link to="/incoming" className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
                View all <ArrowRight size={12} />
              </Link>
            </div>
          )}
        </div>

        {/* Right: Pending Queue + Quick Stats */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* Pending Queue Card */}
          <div className="section-card">
            <div className="section-card-header">
              <h3>Pending Review</h3>
              {pending.length > 0 && <span className="queue-count">{pending.length}</span>}
            </div>
            <div className="section-card-body">
              {pending.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {pending.slice(0, 4).map(exc => {
                    const ctx = exc.context || {};
                    const cls = exc.classification || {};
                    return (
                      <Link key={exc.id} to={`/decisions?exception_id=${exc.id}`}
                        style={{
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                          padding: '8px 12px', borderRadius: '8px', background: 'var(--bg-elevated)',
                          border: '1px solid var(--border)', color: 'var(--text-primary)',
                          fontSize: '13px', textDecoration: 'none', transition: 'border-color 0.15s'
                        }}>
                        <span style={{ fontWeight: 500, textTransform: 'capitalize' }}>
                          {(ctx.exception_type || 'unknown').replace(/_/g, ' ')}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          P{cls.priority || '?'} · ${(ctx.financial_exposure || 0).toLocaleString()}
                        </span>
                      </Link>
                    );
                  })}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '24px 16px', color: 'var(--text-muted)', fontSize: '13px' }}>
                  <CheckCircle size={20} style={{ marginBottom: '8px', color: 'var(--green)' }} />
                  <div>All caught up — no pending reviews</div>
                </div>
              )}
            </div>
            {pending.length > 4 && (
              <div className="section-card-footer">
                <Link to="/decisions" className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
                  View all {pending.length} <ArrowRight size={12} />
                </Link>
              </div>
            )}
          </div>

          {/* Quick Stats Card */}
          <div className="section-card">
            <div className="section-card-header">
              <h3>Quick Stats</h3>
            </div>
            <div className="section-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Approval Rate</span>
                <span style={{ fontSize: '15px', fontWeight: 600 }}>{((stats?.approval_rate || 0) * 100).toFixed(0)}%</span>
              </div>
              <div style={{ height: '4px', background: 'var(--bg-elevated)', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${(stats?.approval_rate || 0) * 100}%`, background: 'var(--green)', borderRadius: '2px', transition: 'width 0.4s ease' }} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <StatMini label="Decisions" value={stats?.total_decisions || 0} />
                <StatMini label="Actions" value={stats?.total_actions || 0} />
                <StatMini label="Completed" value={stats?.completed || 0} />
                <StatMini label="Pending" value={stats?.pending_review || 0} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom: More Exceptions ── */}
      {recent.length > 3 && (
        <div className="section">
          <div className="section-header">
            <span className="section-title">More Exceptions</span>
            <Link to="/incoming" style={{ fontSize: '12px' }}>View all <ArrowRight size={11} /></Link>
          </div>
          <div className="card-grid">
            {recent.slice(3, 6).map(exc => <ExceptionCard key={exc.id} exc={exc} compact />)}
          </div>
        </div>
      )}
    </div>
  );
}

function KPI({ icon, label, value, alert }) {
  return (
    <div className={`kpi-card${alert ? ' kpi-alert' : ''}`}>
      <div className="kpi-icon">{icon}</div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  );
}

function StatMini({ label, value }) {
  return (
    <div style={{ padding: '10px 12px', background: 'var(--bg-elevated)', borderRadius: '8px', border: '1px solid var(--border)' }}>
      <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>{value}</div>
      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{label}</div>
    </div>
  );
}