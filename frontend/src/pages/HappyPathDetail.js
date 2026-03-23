import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Activity, AlertTriangle, TrendingUp } from 'lucide-react';
import api from '../api';

/* ── Shared helpers ─────────────────────────────────────────────────────── */

function Badge({ label, color, bg }) {
  return (
    <span className="badge" style={{ color, background: bg }}>{label}</span>
  );
}

function SLABadge({ status }) {
  const cfg = {
    on_track: { label: 'On Track', color: '#065F46', bg: '#DCFCE7' },
    at_risk:  { label: 'At Risk',  color: '#92400E', bg: '#FEF3C7' },
    critical: { label: 'Critical', color: '#991B1B', bg: '#FEE2E2' },
  }[status] || { label: status, color: '#374151', bg: '#F1F3F7' };
  return <Badge {...cfg} />;
}

function RiskBadge({ level }) {
  const cfg = {
    safe:      { label: 'Safe',      color: '#065F46', bg: '#DCFCE7' },
    this_week: { label: 'This Week', color: '#1E40AF', bg: '#DBEAFE' },
    today:     { label: 'Today',     color: '#92400E', bg: '#FEF3C7' },
    immediate: { label: 'Immediate', color: '#991B1B', bg: '#FEE2E2' },
  }[level] || { label: level, color: '#374151', bg: '#F1F3F7' };
  return <Badge {...cfg} />;
}

function Card({ title, icon: Icon, children, accentColor = '#16A34A' }) {
  return (
    <div className="detail-card" style={{ borderTop: `3px solid ${accentColor}` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        {Icon && <Icon size={16} color={accentColor} />}
        <h3 style={{ margin: 0, color: '#111827' }}>{title}</h3>
      </div>
      {children}
    </div>
  );
}

function PathRow({ label, steps = [], happy }) {
  return (
    <div className="path-row">
      <span className="path-label">{label}:</span>
      <div className="path-steps">
        {steps.map((s, i) => (
          <React.Fragment key={i}>
            <span className={`step${happy ? ' step-happy' : ''}`}>{s}</span>
            {i < steps.length - 1 && <span className="step-arrow">→</span>}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

function ProgressBar({ pct, color }) {
  const p = Math.min(100, Math.max(0, pct));
  const barColor = p >= 80 ? '#DC2626' : p >= 60 ? '#D97706' : '#16A34A';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '8px 0' }}>
      <div style={{ flex: 1, background: '#E5E7EB', borderRadius: 4, height: 8 }}>
        <div style={{ width: `${p}%`, background: color || barColor, height: '100%', borderRadius: 4, transition: 'width 0.3s' }} />
      </div>
      <span style={{ fontSize: '13px', fontWeight: 600, color: color || barColor, minWidth: '36px' }}>{p.toFixed(1)}%</span>
    </div>
  );
}

/* ── Agent steps trace (green themed) ──────────────────────────────────── */

function AgentSteps({ trace }) {
  const [expanded, setExpanded] = useState({});
  if (!trace?.steps?.length) return <div className="trace-empty">No agent trace available.</div>;

  const GREEN_AGENTS = {
    'Context Builder':          { abbr: 'CB', color: '#16A34A', bg: '#DCFCE7' },
    'Path Classifier':          { abbr: 'PC', color: '#0D9488', bg: '#CCFBF1' },
    'Payment Risk Agent':       { abbr: 'PR', color: '#065F46', bg: '#D1FAE5' },
    'SLA Monitor Agent':        { abbr: 'SL', color: '#1E40AF', bg: '#DBEAFE' },
    'Process Optimization Agent': { abbr: 'PO', color: '#6D28D9', bg: '#EDE9FE' },
  };

  const toggle = i => setExpanded(p => ({ ...p, [i]: !p[i] }));

  return (
    <div className="trace-timeline">
      {trace.steps.map((step, idx) => {
        const isConn = step.status === 'connection';
        const cfg = GREEN_AGENTS[step.agent] || { abbr: '??', color: '#6B7280', bg: '#F1F3F7' };
        const hasDetails = !isConn && step.details && Object.keys(step.details).length > 0;
        const isOpen = !!expanded[idx];
        const isLast = idx === trace.steps.length - 1;

        return (
          <div key={idx} className={`trace-step ${isConn ? 'trace-connection' : 'trace-agent'}`}>
            <div className="trace-line-container">
              <div className="trace-dot" style={{ background: isConn ? '#D1D5DB' : cfg.color }} />
              {!isLast && <div className="trace-line" style={{ background: isConn ? '#E5E7EB' : cfg.color + '40' }} />}
            </div>

            {isConn ? (
              <div className="trace-card ac-conn-card">
                <span className="ac-conn-arrow">→</span>
                <span className="ac-conn-text">{step.output}</span>
              </div>
            ) : (
              <div
                className={`trace-card ac-agent-card ${hasDetails ? 'ac-clickable' : ''}`}
                style={{ borderLeft: `3px solid ${cfg.color}` }}
                onClick={() => hasDetails && toggle(idx)}
              >
                <div className="ac-card-top">
                  <div className="ac-avatar" style={{ background: cfg.bg, color: cfg.color }}>{cfg.abbr}</div>
                  <span className="ac-agent-name">{step.agent}</span>
                  <div className="ac-badges">
                    <span className="ac-chip ac-chip-filled">{step.duration_ms ?? 0}ms</span>
                  </div>
                </div>
                <div className="ac-divider" />
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
                {hasDetails && (
                  <div className="ac-expand-hint">
                    <div className="ac-expand-line" />
                    <span>{isOpen ? 'collapse ▴' : 'details ▾'}</span>
                    <div className="ac-expand-line" />
                  </div>
                )}
                {hasDetails && isOpen && (
                  <div className="ac-details">
                    {Object.entries(step.details).map(([k, v]) => (
                      <div key={k} className="ac-detail-row">
                        <span className="ac-detail-key">{k}</span>
                        <span className="ac-detail-val">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
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
  );
}

/* ── Main component ─────────────────────────────────────────────────────── */

export default function HappyPathDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getHappyPathCase(id)
      .then(d => { if (d && !d.error) setData(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="page fade-in"><div className="loading">Loading happy path case…</div></div>;
  if (!data) return <div className="page fade-in"><div className="loading">Case not found.</div></div>;

  const ctx = data.context || {};
  const cls = data.classification || {};
  const insights = data.process_insights || {};
  const pr = insights.payment_risk || {};
  const sla = insights.sla_monitor || {};
  const opt = insights.process_optimization || {};
  const trace = (data.recommended_action_params || {}).agent_trace || null;

  return (
    <div className="page fade-in">
      {/* Header */}
      <div className="page-header">
        <div>
          <Link to="/happy-path" className="back-link"><ArrowLeft size={14} /> Back to Happy Path Cases</Link>
          <h1 style={{ color: '#065F46' }}>Happy Path Detail</h1>
          <p className="page-subtitle" style={{ marginTop: '4px' }}>
            {ctx.vendor} — #{ctx.case_id}
          </p>
        </div>
        <div className="header-badges">
          <span className="badge" style={{ color: '#065F46', background: '#DCFCE7' }}>● Completed</span>
          <SLABadge status={sla.status} />
        </div>
      </div>

      {/* Main grid */}
      <div className="detail-grid">
        {/* Left: Context */}
        <Card title="Context" accentColor="#16A34A">
          <table className="kv-table"><tbody>
            <tr><td className="kv-key">Case ID</td><td>{ctx.case_id}</td></tr>
            <tr><td className="kv-key">Vendor</td><td>{ctx.vendor}</td></tr>
            <tr><td className="kv-key">Team</td><td>{ctx.assigned_team}</td></tr>
            <tr><td className="kv-key">Exposure</td><td>${(ctx.financial_exposure || 0).toLocaleString()}</td></tr>
            <tr><td className="kv-key">Severity</td><td>{ctx.severity_score?.toFixed(2)}</td></tr>
            <tr><td className="kv-key">SLA Hours</td><td>{ctx.sla_hours}h</td></tr>
            <tr><td className="kv-key">Compliance</td><td>{ctx.compliance_flag ? 'Flagged' : 'Clean'}</td></tr>
            <tr><td className="kv-key">Confidence</td><td>{((cls.confidence || 0) * 100).toFixed(0)}%</td></tr>
          </tbody></table>
          <h4 style={{ marginTop: '16px' }}>Process Path</h4>
          <div className="path-display">
            <PathRow label="Actual" steps={ctx.actual_path} />
            <PathRow label="Happy" steps={ctx.happy_path} happy />
          </div>
        </Card>

        {/* Right column: three agent cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Payment Risk */}
          <Card title="Payment Risk" icon={AlertTriangle} accentColor="#D97706">
            {pr.risk_level ? (
              <>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
                  <RiskBadge level={pr.risk_level} />
                  <span style={{ fontSize: '13px', color: '#6B7280' }}>
                    Due in {pr.days_until_due} day(s) · Processing: {pr.historical_processing_days?.toFixed(1)}d
                  </span>
                </div>
                <div style={{ fontSize: '14px', marginBottom: '6px' }}>{pr.insight}</div>
                <div style={{ fontSize: '13px', color: '#374151', padding: '6px 10px', background: '#F9FAFB', borderRadius: 4, borderLeft: '3px solid #D97706' }}>
                  {pr.recommended_action}
                </div>
              </>
            ) : <div className="trace-empty">No payment risk data.</div>}
          </Card>

          {/* SLA Monitor */}
          <Card title="SLA Monitor" icon={Activity} accentColor="#1E40AF">
            {sla.status ? (
              <>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', alignItems: 'center' }}>
                  <SLABadge status={sla.status} />
                  <span style={{ fontSize: '13px', color: '#6B7280' }}>{sla.sla_hours_consumed?.toFixed(1)}h / {sla.sla_hours_total}h</span>
                </div>
                <ProgressBar pct={sla.sla_consumption_pct || 0} />
                <div style={{ fontSize: '14px', marginBottom: '6px', marginTop: '6px' }}>{sla.insight}</div>
                <div style={{ fontSize: '13px', color: '#374151', padding: '6px 10px', background: '#F9FAFB', borderRadius: 4, borderLeft: '3px solid #1E40AF' }}>
                  {sla.recommended_action}
                </div>
              </>
            ) : <div className="trace-empty">No SLA data.</div>}
          </Card>

          {/* Process Optimization */}
          <Card title="Process Optimization" icon={TrendingUp} accentColor="#16A34A">
            {opt.bottleneck_stage ? (
              <>
                <table className="kv-table"><tbody>
                  <tr><td className="kv-key">Bottleneck</td><td><strong>{opt.bottleneck_stage}</strong></td></tr>
                  <tr><td className="kv-key">Current</td><td>{opt.current_stage_time?.toFixed(1)}d</td></tr>
                  <tr><td className="kv-key">Avg</td><td>{opt.avg_stage_time?.toFixed(1)}d</td></tr>
                  <tr><td className="kv-key">Delay</td><td style={{ color: opt.delay_days > 1 ? '#DC2626' : '#065F46' }}>{opt.delay_days?.toFixed(1)}d</td></tr>
                </tbody></table>
                <div style={{ fontSize: '14px', marginTop: '8px', marginBottom: '6px' }}>{opt.insight}</div>
                <div style={{ fontSize: '13px', color: '#374151', padding: '6px 10px', background: '#F9FAFB', borderRadius: 4, borderLeft: '3px solid #16A34A' }}>
                  {opt.recommended_action}
                </div>
              </>
            ) : <div className="trace-empty">No optimization data.</div>}
          </Card>

          {/* Link to process agents */}
          <div style={{ textAlign: 'right' }}>
            <Link
              to={`/process-agents/${ctx.case_id}`}
              style={{ fontSize: '13px', color: '#16A34A', textDecoration: 'underline' }}
            >
              View Agent Recommendations →
            </Link>
          </div>
        </div>
      </div>

      {/* Agent Steps */}
      <div className="detail-card" style={{ marginTop: '16px', borderTop: '3px solid #16A34A' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <h3 style={{ margin: 0, color: '#065F46' }}>Agent Steps</h3>
          {trace && <span className="trace-meta">{trace.trace_id} · {trace.total_steps} steps · {trace.total_duration_ms}ms</span>}
        </div>
        <AgentSteps trace={trace} />
      </div>
    </div>
  );
}
