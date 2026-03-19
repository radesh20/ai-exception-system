import React, { useEffect, useState } from 'react';
import api from '../api';

const AGENTS = {
  'Context Builder': { abbr: 'CB', cls: 'ac-sky' },
  'Root Cause Agent': { abbr: 'RC', cls: 'ac-sand' },
  'Classifier Agent': { abbr: 'CL', cls: 'ac-lavender' },
  'Action Recommender': { abbr: 'AR', cls: 'ac-sage' },
  'Decision Router': { abbr: 'DR', cls: 'ac-rose' },
};

export default function AgentConversation({ exceptionId }) {
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState({});

  useEffect(() => {
    if (!exceptionId) return;
    setLoading(true);
    api.getTrace(exceptionId)
      .then(data => { if (data?.steps) setTrace(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [exceptionId]);

  const toggle = idx => setExpanded(p => ({ ...p, [idx]: !p[idx] }));

  if (loading) return <div className="agent-conversation"><div className="trace-loading">Loading agent conversation…</div></div>;
  if (!trace?.steps) return <div className="agent-conversation"><div className="trace-empty">No agent trace available.</div></div>;

  return (
    <div className="agent-conversation">

      <div className="trace-header">
        <h3>Agent Conversation</h3>
        <span className="trace-meta">{trace.trace_id} · {trace.total_steps} steps · {trace.total_duration_ms}ms</span>
      </div>

      <div className="trace-timeline">
        {trace.steps.map((step, idx) => {
          const isLast = idx === trace.steps.length - 1;
          const isConn = step.status === 'connection';
          const cfg = AGENTS[step.agent] || { abbr: '??', cls: 'ac-gray' };
          const hasDetails = !isConn && step.details && Object.keys(step.details).length > 0;
          const isOpen = !!expanded[idx];

          return (
            <div key={idx} className={`trace-step ${isConn ? 'trace-connection' : 'trace-agent'}`}>

              {/* Rail */}
              <div className="trace-line-container">
                <div className={`trace-dot ${isConn ? 'trace-dot-conn' : cfg.cls}`} />
                {!isLast && <div className={`trace-line ${isConn ? '' : cfg.cls}`} />}
              </div>

              {/* Connection */}
              {isConn && (
                <div className="trace-card ac-conn-card">
                  <span className="ac-conn-arrow">→</span>
                  <span className="ac-conn-text">{step.output}</span>
                  {step.step_number && <span className="ac-step-num">#{step.step_number}</span>}
                </div>
              )}

              {/* Agent card */}
              {!isConn && (
                <div
                  className={`trace-card ac-agent-card ${cfg.cls} ${hasDetails ? 'ac-clickable' : ''}`}
                  onClick={() => hasDetails && toggle(idx)}
                >
                  {/* accent bar */}
                  <div className="ac-accent-bar" />

                  {/* top row */}
                  <div className="ac-card-top">
                    <div className="ac-avatar">{cfg.abbr}</div>
                    <span className="ac-agent-name">{step.agent}</span>
                    <div className="ac-badges">
                      <span className="ac-chip ac-chip-filled">{step.duration_ms ?? 0}ms</span>
                      {step.step_number && <span className="ac-chip ac-chip-outline">#{step.step_number}</span>}
                    </div>
                  </div>

                  {/* divider */}
                  <div className="ac-divider" />

                  {/* IO */}
                  <div className="ac-io">
                    <div className="ac-io-row">
                      <span className="ac-io-label">IN</span>
                      <span className="ac-io-text">{step.input}</span>
                    </div>
                    <div className="ac-io-row">
                      <span className="ac-io-label">OUT</span>
                      <span className="ac-io-text ac-io-out">{step.output}</span>
                    </div>
                  </div>

                  {/* expand hint */}
                  {hasDetails && (
                    <div className="ac-expand-hint">
                      <div className="ac-expand-line" />
                      <span>{isOpen ? 'collapse ▴' : 'details ▾'}</span>
                      <div className="ac-expand-line" />
                    </div>
                  )}

                  {/* details */}
                  {hasDetails && isOpen && (
                    <div className="ac-details">
                      {Object.entries(step.details).map(([key, val]) => (
                        <div key={key} className="ac-detail-row">
                          <span className="ac-detail-key">{key}</span>
                          <span className="ac-detail-val">
                            {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

            </div>
          );
        })}
      </div>
    </div>
  );
}