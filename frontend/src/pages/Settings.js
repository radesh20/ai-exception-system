import React from 'react';
import { Settings as SettingsIcon } from 'lucide-react';

export default function Settings({ config }) {
  if (!config) return <div className="page fade-in"><div className="loading">Loading config...</div></div>;

  const integrations = [
    { key: 'Microsoft Teams', val: config.teams_enabled, desc: 'Teams webhook alerts' },
    { key: 'Microsoft Outlook', val: config.outlook_enabled, desc: 'Outlook email via Graph API' },
    { key: 'Slack MCP', val: config.slack_enabled, desc: 'Slack via MCP server' },
    { key: 'Gmail MCP', val: config.gmail_enabled, desc: 'Gmail via MCP server' },
    { key: 'ServiceNow', val: config.servicenow_enabled, desc: 'Create ServiceNow tickets' },
  ];

  const system = [
    { key: 'Azure GPT-4o (Deep Agent)', val: config.azure_enabled, desc: 'AI-powered analysis' },
    { key: 'Celonis Mode', val: config.celonis_mode, desc: 'Data source (mock = sample data)' },
    { key: 'Storage Backend', val: config.storage_backend, desc: 'Where data is stored' },
    { key: 'Execution Mode', val: config.execution_mode, desc: 'Where actions execute' },
    { key: 'Learning Engine', val: config.learning_enabled, desc: 'Improve AI from decisions' },
  ];

  const enabledCount = [config.teams_enabled, config.outlook_enabled, config.slack_enabled, config.gmail_enabled, config.servicenow_enabled].filter(Boolean).length;

  return (
    <div className="page fade-in">
      {/* ── Header ── */}
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <p className="page-subtitle">Current configuration. Change in <code>.env</code> and restart API.</p>
        </div>
      </div>

      {/* ── Summary ── */}
      <div className="stat-row">
        <div className="inline-stat">
          <span className="inline-stat-value">{enabledCount}</span>
          <span className="inline-stat-label">Integrations Active</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value" style={{ textTransform: 'capitalize' }}>{config.celonis_mode || '—'}</span>
          <span className="inline-stat-label">Data Source</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value" style={{ textTransform: 'uppercase' }}>{config.storage_backend || '—'}</span>
          <span className="inline-stat-label">Storage</span>
        </div>
      </div>

      {/* ── System Settings ── */}
      <div className="section">
        <div className="section-header">
          <span className="section-title">System Configuration</span>
        </div>
        <div className="section-card">
          {system.map(({ key, val, desc }) => (
            <SettingRow key={key} name={key} desc={desc} val={val} />
          ))}
        </div>
      </div>

      {/* ── Integrations ── */}
      <div className="section">
        <div className="section-header">
          <span className="section-title">Integrations</span>
          <span className="section-meta">{enabledCount} of {integrations.length} enabled</span>
        </div>
        <div className="section-card">
          {integrations.map(({ key, val, desc }) => (
            <SettingRow key={key} name={key} desc={desc} val={val} />
          ))}
        </div>
      </div>
    </div>
  );
}

function SettingRow({ name, desc, val }) {
  return (
    <div className="setting-item">
      <div className="setting-info">
        <div className="setting-name">{name}</div>
        <div className="setting-desc">{desc}</div>
      </div>
      <div className="setting-value">
        {typeof val === 'boolean' ? (
          <span className={`pill ${val ? 'pill-green' : 'pill-gray'}`}>
            {val ? 'Enabled' : 'Disabled'}
          </span>
        ) : (
          <span className="pill pill-blue">{String(val || 'not set')}</span>
        )}
      </div>
    </div>
  );
}