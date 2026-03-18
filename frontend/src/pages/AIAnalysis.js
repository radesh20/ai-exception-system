import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

export default function AIAnalysis() {
  const [exceptions, setExceptions] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    api.getExceptions({ limit: 20 }).then(d => {
      if (Array.isArray(d)) setExceptions(d);
    }).catch(() => {});
  }, []);

  return (
    <div className="page">
      <h1>🤖 AI Analysis</h1>
      <p className="page-desc">Deep Agents analyze each exception — root cause, confidence, recommended action.</p>

      <div className="analysis-layout">
        <div className="analysis-list">
          {exceptions.map(exc => (
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
          ))}
        </div>

        <div className="analysis-detail">
          {selected ? <AnalysisDetail exc={selected} /> : (
            <div className="empty-state">← Select an exception to see AI analysis</div>
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
        <Link to={`/exception/${exc.id}`} className="btn-secondary">Full Details →</Link>
      </div>

      <div className="analysis-section">
        <h4>🔍 Root Cause Hypothesis</h4>
        <div className="hypothesis">{rc.hypothesis || 'Analysis pending'}</div>
        <ConfBar confidence={rc.confidence || 0} />
      </div>

      <div className="analysis-section">
        <h4>📊 Classification</h4>
        <table className="kv-table"><tbody>
          <tr><td className="kv-key">Category</td><td>{(cls.category || '').replace(/_/g, ' ')}</td></tr>
          <tr><td className="kv-key">Priority</td><td>P{cls.priority || '?'}/5</td></tr>
          <tr><td className="kv-key">Novel</td><td>{cls.is_novel ? '⚠️ Yes' : 'No'}</td></tr>
          <tr><td className="kv-key">Routing</td><td>
            <span className={`route-tag route-${cls.routing}`}>{cls.routing}</span>
          </td></tr>
        </tbody></table>
      </div>

      <div className="analysis-section">
        <h4>⚡ Recommended Action</h4>
        <div className="rec-action">{(exc.recommended_action || '').replace(/_/g, ' ')}</div>
        <div className="reasoning">{exc.ai_reasoning}</div>
      </div>

      {rc.causal_factors?.length > 0 && (
        <div className="analysis-section">
          <h4>🔗 Causal Factors</h4>
          <ul className="factors-list">
            {rc.causal_factors.map((f, i) => <li key={i}>{f}</li>)}
          </ul>
        </div>
      )}

      {rc.supporting_cases?.length > 0 && (
        <div className="analysis-section">
          <h4>📂 Supporting Cases</h4>
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
  const color = pct >= 70 ? '#198754' : pct >= 40 ? '#ffc107' : '#dc3545';
  return (
    <div className="conf-bar-wrap">
      <div className="conf-bar">
        <div className="conf-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="conf-label" style={{ color }}>{pct}% confidence</span>
    </div>
  );
}