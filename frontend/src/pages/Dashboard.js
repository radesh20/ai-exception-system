import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import ExceptionCard from '../components/ExceptionCard';

export default function Dashboard({ config }) {
  const [stats, setStats] = useState(null);
  const [pending, setPending] = useState([]);
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    api.getStats().then(s => { if (s) setStats(s); }).catch(() => {});
    api.getPending().then(d => { if (Array.isArray(d)) setPending(d); }).catch(() => {});
    api.getExceptions({ limit: 6 }).then(d => { if (Array.isArray(d)) setRecent(d); }).catch(() => {});
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <h1>📊 Dashboard</h1>
        <button className="btn-secondary" onClick={() => {
          api.processAll().then(() => {
            api.getStats().then(setStats);
            api.getExceptions({ limit: 6 }).then(setRecent);
            api.getPending().then(setPending);
          });
        }}>🔄 Process All Open</button>
      </div>

      {config && (
        <div className="config-pills">
          <span className={`pill ${config.azure_enabled ? 'pill-green' : 'pill-gray'}`}>
            🧠 {config.azure_enabled ? 'Deep Agent' : 'Rule-Based'}
          </span>
          <span className={`pill ${config.teams_enabled ? 'pill-green' : 'pill-gray'}`}>
            💬 Teams: {config.teams_enabled ? 'On' : 'Off'}
          </span>
          <span className={`pill ${config.outlook_enabled ? 'pill-green' : 'pill-gray'}`}>
            📧 Outlook: {config.outlook_enabled ? 'On' : 'Off'}
          </span>
          <span className={`pill ${config.slack_enabled ? 'pill-green' : 'pill-gray'}`}>
            💬 Slack: {config.slack_enabled ? 'On' : 'Off'}
          </span>
          <span className={`pill ${config.gmail_enabled ? 'pill-green' : 'pill-gray'}`}>
            📧 Gmail: {config.gmail_enabled ? 'On' : 'Off'}
          </span>
          <span className="pill pill-blue">🗄️ {config.storage_backend?.toUpperCase()}</span>
          <span className={`pill ${config.servicenow_enabled ? 'pill-green' : 'pill-gray'}`}>
            🎫 ServiceNow: {config.servicenow_enabled ? 'On' : 'Off'}
          </span>
        </div>
      )}

      <div className="kpi-grid">
        <KPI icon="🔢" label="Total Exceptions" value={stats?.total_exceptions || 0} />
        <KPI icon="⏳" label="Pending Review" value={stats?.pending_review || 0} alert={stats?.pending_review > 0} />
        <KPI icon="✅" label="Completed" value={stats?.completed || 0} />
        <KPI icon="📈" label="Approval Rate" value={`${((stats?.approval_rate || 0) * 100).toFixed(0)}%`} />
        <KPI icon="👤" label="Total Decisions" value={stats?.total_decisions || 0} />
        <KPI icon="⚡" label="Actions Executed" value={stats?.total_actions || 0} />
      </div>

      {pending.length > 0 && (
        <div className="alert-banner">
          🚨 {pending.length} exception{pending.length > 1 ? 's' : ''} need human review!{' '}
          <Link to="/decisions">Review Now →</Link>
        </div>
      )}

      <h2>Recent Exceptions</h2>
      <div className="card-grid">
        {recent.map(exc => <ExceptionCard key={exc.id} exc={exc} compact />)}
        {recent.length === 0 && (
          <div className="empty-state">
            <p>No exceptions yet. Run <code>python main.py</code> first.</p>
          </div>
        )}
      </div>
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