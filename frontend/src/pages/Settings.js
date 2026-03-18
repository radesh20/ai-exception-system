import React from 'react';

export default function Settings({ config }) {
  if (!config) return <div className="page"><div className="loading">Loading config...</div></div>;

  const items = [
    { key: 'Azure GPT-4o (Deep Agent)', val: config.azure_enabled, desc: 'AI-powered analysis' },
    { key: 'Celonis Mode', val: config.celonis_mode, desc: 'Data source (mock = sample data)' },
    { key: 'Storage Backend', val: config.storage_backend, desc: 'Where data is stored' },
    { key: 'Microsoft Teams', val: config.teams_enabled, desc: 'Teams webhook alerts' },
    { key: 'Microsoft Outlook', val: config.outlook_enabled, desc: 'Outlook email via Graph API' },
    { key: 'Slack MCP', val: config.slack_enabled, desc: 'Slack via MCP server' },
    { key: 'Gmail MCP', val: config.gmail_enabled, desc: 'Gmail via MCP server' },
    { key: 'Execution Mode', val: config.execution_mode, desc: 'Where actions execute' },
    { key: 'ServiceNow', val: config.servicenow_enabled, desc: 'Create ServiceNow tickets' },
    { key: 'Learning Engine', val: config.learning_enabled, desc: 'Improve AI from decisions' },
  ];

  return (
    <div className="page">
      <h1>⚙️ Settings</h1>
      <p className="page-desc">Current configuration. Change in <code>.env</code> and restart API.</p>

      <div className="settings-grid">
        {items.map(({ key, val, desc }) => (
          <div key={key} className="setting-item">
            <div className="setting-info">
              <div className="setting-name">{key}</div>
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
        ))}
      </div>
    </div>
  );
}