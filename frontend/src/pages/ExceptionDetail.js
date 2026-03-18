import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import { StatusBadge, PriorityBadge } from '../components/StatusBadge';
import DecisionForm from '../components/DecisionForm';

export default function ExceptionDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);

  const load = () => api.getException(id).then(d => { if (d) setData(d); }).catch(() => {});
  useEffect(() => { load(); }, [id]);

  if (!data) return <div className="page"><div className="loading">Loading...</div></div>;

  const ctx = data.context || {};
  const cls = data.classification || {};
  const rc = data.root_cause || {};

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/" className="back-link">← Back</Link>
          <h1>Exception Detail</h1>
        </div>
        <div className="header-badges">
          <StatusBadge status={data.status} />
          <PriorityBadge priority={cls.priority} />
        </div>
      </div>

      <div className="detail-grid">
        <Card title="📋 Context">
          <table className="kv-table"><tbody>
            <tr><td className="kv-key">ID</td><td className="mono">{data.id}</td></tr>
            <tr><td className="kv-key">Case ID</td><td>{ctx.case_id}</td></tr>
            <tr><td className="kv-key">Type</td><td>{(ctx.exception_type || '').replace(/_/g, ' ')}</td></tr>
            <tr><td className="kv-key">Exposure</td><td>${(ctx.financial_exposure || 0).toLocaleString()}</td></tr>
            <tr><td className="kv-key">Severity</td><td>{ctx.severity_score?.toFixed(2)}</td></tr>
            <tr><td className="kv-key">Vendor</td><td>{ctx.vendor}</td></tr>
            <tr><td className="kv-key">Team</td><td>{ctx.assigned_team}</td></tr>
            <tr><td className="kv-key">Compliance</td><td>{ctx.compliance_flag ? '⚠️ Flagged' : 'Clean'}</td></tr>
          </tbody></table>

          <h4 style={{marginTop:'12px'}}>Process Path</h4>
          <div className="path-display">
            <PathRow label="Actual" steps={ctx.actual_path} deviation={ctx.deviation_point} />
            <PathRow label="Happy" steps={ctx.happy_path} happy />
          </div>
        </Card>

        <Card title="🤖 AI Analysis">
          <div className="hypothesis-box">{rc.hypothesis || 'No analysis'}</div>
          <ConfBar confidence={rc.confidence || 0} />
          {rc.causal_factors?.map((f, i) => (
            <div key={i} className="causal-factor">→ {f}</div>
          ))}
          {rc.supporting_cases?.length > 0 && (
            <div style={{marginTop:'8px'}}>
              <strong>Supporting:</strong>{' '}
              {rc.supporting_cases.map(c => <span key={c} className="case-tag">{c}</span>)}
            </div>
          )}
        </Card>

        <Card title="⚡ Recommendation">
          <div className="rec-box">{(data.recommended_action || '').replace(/_/g, ' ')}</div>
          <div className="reasoning-text">{data.ai_reasoning}</div>
          <table className="kv-table" style={{marginTop:'8px'}}><tbody>
            <tr><td className="kv-key">Category</td><td>{(cls.category || '').replace(/_/g, ' ')}</td></tr>
            <tr><td className="kv-key">Routing</td><td>
              <span className={`route-tag route-${cls.routing}`}>{cls.routing}</span>
            </td></tr>
            <tr><td className="kv-key">Confidence</td><td>{((cls.confidence || 0) * 100).toFixed(0)}%</td></tr>
            <tr><td className="kv-key">Novel</td><td>{cls.is_novel ? '⚠️ Yes' : 'No'}</td></tr>
          </tbody></table>
        </Card>

        {data.status === 'pending_decision' && (
          <Card title="👤 Make Decision">
            <DecisionForm exception={data} onComplete={load} />
          </Card>
        )}

        {data.decisions?.length > 0 && (
          <Card title="📝 Decision History">
            {data.decisions.map(d => (
              <div key={d.id} className="decision-history-item">
                <span className={`dec-type dec-${d.decision_type}`}>{d.decision_type}</span>
                <span>{d.final_action}</span>
                <span>by <strong>{d.analyst_name}</strong></span>
                {d.notes && <div className="dec-notes">{d.notes}</div>}
              </div>
            ))}
          </Card>
        )}

        {data.actions?.length > 0 && (
          <Card title="⚡ Executed Actions">
            {data.actions.map(a => (
              <div key={a.id} className="action-item">
                <span className="action-type">{(a.action_type || '').replace(/_/g, ' ')}</span>
                <span className={`action-status status-${a.status}`}>{a.status}</span>
                <span className={`target-badge target-${a.execution_target}`}>{a.execution_target}</span>
                <div className="action-result">{a.result?.message || a.result?.error || ''}</div>
              </div>
            ))}
          </Card>
        )}
      </div>
    </div>
  );
}

function Card({ title, children }) {
  return <div className="detail-card"><h3>{title}</h3>{children}</div>;
}

function PathRow({ label, steps = [], deviation, happy }) {
  return (
    <div className="path-row">
      <span className="path-label">{label}:</span>
      <div className="path-steps">
        {steps.map((s, i) => (
          <React.Fragment key={i}>
            <span className={`step${s === deviation ? ' step-deviation' : happy ? ' step-happy' : ''}`}>{s}</span>
            {i < steps.length - 1 && <span className="step-arrow">→</span>}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

function ConfBar({ confidence }) {
  const pct = Math.round(confidence * 100);
  const color = pct >= 70 ? '#198754' : pct >= 40 ? '#ffc107' : '#dc3545';
  return (
    <div className="conf-row">
      <div className="conf-bar">
        <div style={{ width: `${pct}%`, background: color, height: '100%', borderRadius: 4 }} />
      </div>
      <span style={{ color, fontWeight: 600 }}>{pct}%</span>
    </div>
  );
}