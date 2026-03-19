import React, { useEffect, useState } from 'react';
import api from '../api';

const AGENT_COLORS = {
  'Context Builder':    { bg: '#e7f3ff', border: '#0d6efd', icon: '📋' },
  'Root Cause Agent':   { bg: '#fff3cd', border: '#ffc107', icon: '🔍' },
  'Classifier Agent':   { bg: '#f0e7ff', border: '#8b5cf6', icon: '📊' },
  'Action Recommender': { bg: '#d4edda', border: '#198754', icon: '⚡' },
  'Decision Router':    { bg: '#f8d7da', border: '#dc3545', icon: '🚦' },
};

const CONNECTION_STYLE = {
  bg: '#f8f9fa',
  border: '#adb5bd',
  icon: '→',
};

export default function AgentConversation({ exceptionId }) {
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState({});

  useEffect(() => {
    if (!exceptionId) return;
    setLoading(true);
    api.getTrace(exceptionId)
      .then(data => {
        if (data && data.steps) setTrace(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [exceptionId]);

  const toggleExpand = (idx) => {
    setExpanded(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  if (loading) return <div className="trace-loading">Loading agent conversation...</div>;
  if (!trace || !trace.steps) return <div className="trace-empty">No agent trace available.</div>;

  return (
    <div className="agent-conversation">
      <div className="trace-header">
        <h3>🤖 Agent Conversation</h3>
        <span className="trace-meta">
          Trace: {trace.trace_id} | {trace.total_steps} steps | {trace.total_duration_ms}ms
        </span>
      </div>

      <div className="trace-timeline">
        {trace.steps.map((step, idx) => {
          const isConnection = step.status === 'connection';
          const style = isConnection
            ? CONNECTION_STYLE
            : (AGENT_COLORS[step.agent] || { bg: '#f8f9fa', border: '#6c757d', icon: '🤖' });

          return (
            <div key={idx} className={`trace-step ${isConnection ? 'trace-connection' : 'trace-agent'}`}>
              <div className="trace-line-container">
                <div className="trace-dot" style={{ background: style.border }} />
                {idx < trace.steps.length - 1 && <div className="trace-line" />}
              </div>

              <div
                className="trace-card"
                style={{ background: style.bg, borderLeft: `4px solid ${style.border}` }}
                onClick={() => !isConnection && toggleExpand(idx)}
              >
                <div className="trace-card-header">
                  <span className="trace-icon">{style.icon}</span>
                  <span className="trace-agent-name">{step.agent}</span>
                  {!isConnection && (
                    <span className="trace-duration">{step.duration_ms}ms</span>
                  )}
                  {step.step_number && (
                    <span className="trace-step-num">#{step.step_number}</span>
                  )}
                </div>

                {!isConnection && (
                  <div className="trace-io">
                    <div className="trace-input">
                      <span className="trace-label">📥 Input:</span>
                      <span>{step.input}</span>
                    </div>
                    <div className="trace-output">
                      <span className="trace-label">📤 Output:</span>
                      <span>{step.output}</span>
                    </div>
                  </div>
                )}

                {isConnection && (
                  <div className="trace-connection-msg">{step.output}</div>
                )}

                {!isConnection && expanded[idx] && step.details && (
                  <div className="trace-details">
                    <h5>Details</h5>
                    {Object.entries(step.details).map(([key, val]) => (
                      <div key={key} className="trace-detail-row">
                        <span className="trace-detail-key">{key}:</span>
                        <span className="trace-detail-val">
                          {typeof val === 'object'
                            ? JSON.stringify(val, null, 2)
                            : String(val)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {!isConnection && !expanded[idx] && step.details && Object.keys(step.details).length > 0 && (
                  <div className="trace-expand-hint">Click to see details ▼</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}