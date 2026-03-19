import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import api from '../api';
import { StatusBadge, PriorityBadge } from '../components/StatusBadge';
import DecisionForm from '../components/DecisionForm';
import AgentConversation from '../components/AgentConversation';

export default function ExceptionDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);

  const load = () => api.getException(id).then(d => { if (d) setData(d); }).catch(() => { });
  useEffect(() => { load(); }, [id]);

  if (!data) return <div className="page fade-in"><div className="loading">Loading exception...</div></div>;

  const ctx = data.context || {};
  const cls = data.classification || {};
  const rc = data.root_cause || {};

  return (
    <div className="page fade-in">
      {/* ── Header ── */}
      <div className="page-header">
        <div>
          <Link to="/" className="back-link"><ArrowLeft size={14} /> Back to Dashboard</Link>
          <h1>Exception Detail</h1>
          <p className="page-subtitle" style={{ marginTop: '4px' }}>
            {(ctx.exception_type || '').replace(/_/g, ' ')} — #{data.id?.slice(0, 12)}
          </p>
        </div>
        <div className="header-badges">
          <StatusBadge status={data.status} />
          <PriorityBadge priority={cls.priority} />
        </div>
      </div>

      {/* ── Summary Stats ── */}
      <div className="stat-row">
        <div className="inline-stat">
          <span className="inline-stat-value">${(ctx.financial_exposure || 0).toLocaleString()}</span>
          <span className="inline-stat-label">Exposure</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value">{ctx.severity_score?.toFixed(1) || '—'}</span>
          <span className="inline-stat-label">Severity</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value">{((cls.confidence || 0) * 100).toFixed(0)}%</span>
          <span className="inline-stat-label">AI Confidence</span>
        </div>
        <div className="inline-stat">
          <span className="inline-stat-value" style={{ textTransform: 'capitalize' }}>{cls.routing || '—'}</span>
          <span className="inline-stat-label">Routing</span>
        </div>
      </div>

      {/* ── Main Grid ── */}
      <div className="detail-grid">
        <Card title="Context">
          <table className="kv-table"><tbody>
            <tr><td className="kv-key">ID</td><td className="mono">{data.id}</td></tr>
            <tr><td className="kv-key">Case ID</td><td>{ctx.case_id}</td></tr>
            <tr><td className="kv-key">Type</td><td>{(ctx.exception_type || '').replace(/_/g, ' ')}</td></tr>
            <tr><td className="kv-key">Exposure</td><td>${(ctx.financial_exposure || 0).toLocaleString()}</td></tr>
            <tr><td className="kv-key">Severity</td><td>{ctx.severity_score?.toFixed(2)}</td></tr>
            <tr><td className="kv-key">Vendor</td><td>{ctx.vendor}</td></tr>
            <tr><td className="kv-key">Team</td><td>{ctx.assigned_team}</td></tr>
            <tr><td className="kv-key">Compliance</td><td>{ctx.compliance_flag ? 'Flagged' : 'Clean'}</td></tr>
          </tbody></table>

          <h4 style={{ marginTop: '16px' }}>Process Path</h4>
          <div className="path-display">
            <PathRow label="Actual" steps={ctx.actual_path} deviation={ctx.deviation_point} />
            <PathRow label="Happy" steps={ctx.happy_path} happy />
          </div>
        </Card>

        <Card title="AI Analysis">
          <div className="hypothesis-box">{rc.hypothesis || 'No analysis'}</div>
          <ConfBar confidence={rc.confidence || 0} />
          {rc.causal_factors?.map((f, i) => (
            <div key={i} className="causal-factor">→ {f}</div>
          ))}
          {rc.supporting_cases?.length > 0 && (
            <div style={{ marginTop: '8px' }}>
              <strong>Supporting:</strong>{' '}
              {rc.supporting_cases.map(c => <span key={c} className="case-tag">{c}</span>)}
            </div>
          )}
        </Card>

        <Card title="Recommendation">
          <div className="rec-box">{(data.recommended_action || '').replace(/_/g, ' ')}</div>
          <div className="reasoning-text">{data.ai_reasoning}</div>
          <table className="kv-table" style={{ marginTop: '8px' }}><tbody>
            <tr><td className="kv-key">Category</td><td>{(cls.category || '').replace(/_/g, ' ')}</td></tr>
            <tr><td className="kv-key">Routing</td><td>
              <span className={`route-tag route-${cls.routing}`}>{cls.routing}</span>
            </td></tr>
            <tr><td className="kv-key">Confidence</td><td>{((cls.confidence || 0) * 100).toFixed(0)}%</td></tr>
            <tr><td className="kv-key">Novel</td><td>{cls.is_novel ? 'Yes' : 'No'}</td></tr>
          </tbody></table>
        </Card>

        {data.status === 'pending_decision' && (
          <Card title="Make Decision">
            <DecisionForm exception={data} onComplete={load} />
          </Card>
        )}

        {data.erp_recommendation && (
          <ErpCard
            exceptionId={data.id}
            erp={data.erp_recommendation}
            status={data.erp_execution_status}
            onUpdate={load}
          />
        )}

        {data.decisions?.length > 0 && (
          <Card title="Decision History">
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
          <Card title="Executed Actions">
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

        {/* ── Agent Conversation Trace ── */}
        <div className="detail-card" style={{ gridColumn: '1 / -1' }}>
          <AgentConversation exceptionId={data.id} />
        </div>
      </div>
    </div>
  );
}

function Card({ title, children }) {
  return <div className="detail-card"><h3>{title}</h3>{children}</div>;
}

function ErpCard({ exceptionId, erp, status, onUpdate }) {
  const [busy, setBusy] = React.useState(false);
  const [msg, setMsg] = React.useState('');
  const [analyst, setAnalyst] = React.useState('');

  const handleApprove = async () => {
    if (!analyst.trim()) { setMsg('Please enter your name before approving.'); return; }
    setBusy(true);
    setMsg('');
    try {
      await api.approveErpAction(exceptionId, { analyst_name: analyst });
      setMsg('ERP action approved.');
      onUpdate();
    } catch (e) {
      setMsg('Failed to approve ERP action.');
    } finally {
      setBusy(false);
    }
  };

  const handleReject = async () => {
    if (!analyst.trim()) { setMsg('Please enter your name before rejecting.'); return; }
    setBusy(true);
    setMsg('');
    try {
      await api.rejectErpAction(exceptionId, { analyst_name: analyst });
      setMsg('ERP action rejected.');
      onUpdate();
    } catch (e) {
      setMsg('Failed to reject ERP action.');
    } finally {
      setBusy(false);
    }
  };

  const statusColor = { pending: '#D97706', approved: '#0D9488', rejected: '#DC2626', executed: '#6366F1' };
  const color = statusColor[status] || '#6B7280';

  return (
    <Card title="ERP Action Required">
      <table className="kv-table"><tbody>
        <tr><td className="kv-key">System</td><td>{erp.system || 'SAP'}</td></tr>
        <tr><td className="kv-key">Transaction</td><td><strong>{erp.transaction}</strong></td></tr>
        <tr><td className="kv-key">Description</td><td>{erp.description}</td></tr>
        <tr><td className="kv-key">Estimated Impact</td><td>{erp.estimated_impact}</td></tr>
        <tr><td className="kv-key">Approval Required</td><td>{erp.requires_approval ? 'Yes' : 'No'}</td></tr>
        <tr>
          <td className="kv-key">Status</td>
          <td><span style={{ color, fontWeight: 600, textTransform: 'capitalize' }}>{status || 'pending'}</span></td>
        </tr>
      </tbody></table>
      {status === 'pending' && (
        <div style={{ marginTop: '12px' }}>
          <input
            type="text"
            placeholder="Your name"
            value={analyst}
            onChange={e => setAnalyst(e.target.value)}
            style={{ display: 'block', marginBottom: '8px', padding: '4px 8px', borderRadius: 4, border: '1px solid #ccc', width: '200px' }}
          />
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className="btn btn-primary"
              onClick={handleApprove}
              disabled={busy}
              style={{ background: '#0D9488', color: '#fff', border: 'none', padding: '6px 14px', borderRadius: 4, cursor: 'pointer' }}
            >
              Approve ERP Action
            </button>
            <button
              className="btn btn-secondary"
              onClick={handleReject}
              disabled={busy}
              style={{ background: '#DC2626', color: '#fff', border: 'none', padding: '6px 14px', borderRadius: 4, cursor: 'pointer' }}
            >
              Reject ERP Action
            </button>
          </div>
        </div>
      )}
      {msg && <div style={{ marginTop: '8px', fontSize: '13px', color: '#6B7280' }}>{msg}</div>}
    </Card>
  );
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
  const color = pct >= 70 ? '#0D9488' : pct >= 40 ? '#D97706' : '#DC2626';
  return (
    <div className="conf-row">
      <div className="conf-bar">
        <div style={{ width: `${pct}%`, background: color, height: '100%', borderRadius: 4 }} />
      </div>
      <span style={{ color, fontWeight: 600, fontSize: '13px' }}>{pct}%</span>
    </div>
  );
}