import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Brain, ArrowRight } from 'lucide-react';
import api from '../api';

export default function AIAnalysis() {
  const [exceptions, setExceptions] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    api.getExceptions({ limit: 20 }).then(d => {
      if (Array.isArray(d)) setExceptions(d);
    }).catch(() => { });
  }, []);

  // Compute routing stats
  const autoCount = exceptions.filter(e => e.classification?.routing === 'auto').length;
  const humanCount = exceptions.filter(e => e.classification?.routing === 'human').length;

  return (
    <div className="page fade-in">
      {/* ── Header ── */}
      <div className="page-header">
        <div>
          <h1>AI Analysis</h1>
          <p className="page-subtitle">Deep Agents analyze each exception — root cause, confidence, recommended action.</p>
        </div>
      </div>

      {/* ── Summary Stats ── */}
      <div className="stat-row">
        <div className="inline-stat">
          <span className="inline-stat-value">{exceptions.length}</span>
          <span className="inline-stat-label">Analyzed</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value">{autoCount}</span>
          <span className="inline-stat-label">Auto-routed</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value">{humanCount}</span>
          <span className="inline-stat-label">Human review</span>
        </div>
      </div>

      {/* ── Main Layout ── */}
      <div className="analysis-layout">
        <div className="analysis-list">
          {exceptions.length === 0 ? (
            <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
              <Brain size={20} style={{ marginBottom: '8px', opacity: 0.5 }} />
              <div>No exceptions analyzed yet</div>
            </div>
          ) : (
            exceptions.map(exc => (
              <div key={exc.id}
                className={`analysis-item${selected?.id === exc.id ? ' active' : ''}`}
                onClick={() => setSelected(exc)}>
                <div className="ai-item-type">
                  {(exc.context?.exception_type || 'unknown').replace(/_/g, ' ')}
                </div>
                <div className="ai-item-meta">
                  <span>P{exc.classification?.priority || '?'}</span>
                  <span>{((exc.classification?.confidence || 0) * 100).toFixed(0)}% conf</span>
                  <span className={`route-tag route-${exc.classification?.routing || 'human'}`}>
                    {exc.classification?.routing || 'pending'}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="analysis-detail">
          {selected ? <AnalysisDetail exc={selected} /> : (
            <div className="empty-state" style={{ border: 'none' }}>
              <div className="empty-state-icon"><Brain size={20} /></div>
              <div className="empty-state-title">Select an exception</div>
              <div className="empty-state-desc">Click an item from the list to view its AI analysis details</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AnalysisDetail({ exc }) {
  const rc = exc.root_cause || {};
  const cls = exc.classification || {};
  const ctx = exc.context || {};

  return (
    <div>
      <div className="detail-header">
        <h3>{(ctx.exception_type || '').replace(/_/g, ' ')}</h3>
        <Link to={`/exception/${exc.id}`} className="btn-secondary">
          Full Details <ArrowRight size={13} />
        </Link>
      </div>

      <div className="analysis-section">
        <h4>Root Cause Hypothesis</h4>
        <div className="hypothesis">{rc.hypothesis || 'Analysis pending'}</div>
        <ConfBar confidence={rc.confidence || 0} />
      </div>

      <div className="analysis-section">
        <h4>Classification</h4>
        <table className="kv-table"><tbody>
          <tr><td className="kv-key">Category</td><td>{(cls.category || '').replace(/_/g, ' ')}</td></tr>
          <tr><td className="kv-key">Priority</td><td>P{cls.priority || '?'}/5</td></tr>
          <tr><td className="kv-key">Novel</td><td>{cls.is_novel ? 'Yes' : 'No'}</td></tr>
          <tr><td className="kv-key">Routing</td><td>
            <span className={`route-tag route-${cls.routing}`}>{cls.routing}</span>
          </td></tr>
        </tbody></table>
      </div>

      <div className="analysis-section">
        <h4>Recommended Action</h4>
        <div className="rec-action">{(exc.recommended_action || '').replace(/_/g, ' ')}</div>
        <div className="reasoning">{exc.ai_reasoning}</div>
      </div>

      {rc.causal_factors?.length > 0 && (
        <div className="analysis-section">
          <h4>Causal Factors</h4>
          <ul className="factors-list">
            {rc.causal_factors.map((f, i) => <li key={i}>{f}</li>)}
          </ul>
        </div>
      )}

      {rc.supporting_cases?.length > 0 && (
        <div className="analysis-section">
          <h4>Supporting Cases</h4>
          <div className="supporting-cases">
            {rc.supporting_cases.map(c => <span key={c} className="case-tag">{c}</span>)}
          </div>
        </div>
      )}
    </div>
  );
}

function ConfBar({ confidence }) {
  const pct = Math.round(confidence * 100);
  const color = pct >= 70 ? '#34d399' : pct >= 40 ? '#fbbf24' : '#f87171';
  return (
    <div className="conf-bar-wrap">
      <div className="conf-bar">
        <div className="conf-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="conf-label" style={{ color }}>{pct}% confidence</span>
    </div>
  );
}