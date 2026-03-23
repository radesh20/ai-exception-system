import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle, AlertTriangle, Clock, TrendingUp } from 'lucide-react';
import api from '../api';

const SLA_BADGE = {
  on_track: { label: 'On Track', color: '#065F46', bg: '#DCFCE7' },
  at_risk:  { label: 'At Risk',  color: '#92400E', bg: '#FEF3C7' },
  critical: { label: 'Critical', color: '#991B1B', bg: '#FEE2E2' },
};

const RISK_BADGE = {
  safe:      { label: 'Safe',      color: '#065F46', bg: '#DCFCE7' },
  this_week: { label: 'This Week', color: '#1E40AF', bg: '#DBEAFE' },
  today:     { label: 'Today',     color: '#92400E', bg: '#FEF3C7' },
  immediate: { label: 'Immediate', color: '#991B1B', bg: '#FEE2E2' },
};

function Badge({ config, value }) {
  const cfg = (config || {})[value] || { label: value, color: '#374151', bg: '#F1F3F7' };
  return (
    <span className="badge" style={{ color: cfg.color, background: cfg.bg }}>
      {cfg.label}
    </span>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="stat-card" style={{ borderTop: `3px solid ${color}` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
        <Icon size={16} color={color} />
        <span className="stat-label">{label}</span>
      </div>
      <div className="stat-value" style={{ color }}>{value}</div>
    </div>
  );
}

export default function HappyPathCases() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getHappyPathCases()
      .then(d => { if (d) setData(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page fade-in"><div className="loading">Loading happy path cases…</div></div>;

  const summary = data?.summary || {};
  const cases = data?.cases || [];

  return (
    <div className="page fade-in">
      <div className="page-header">
        <div>
          <h1 style={{ color: '#065F46' }}>Happy Path Cases</h1>
          <p className="page-subtitle">Cases that completed the full P2P happy path successfully</p>
        </div>
        <span className="badge" style={{ color: '#065F46', background: '#DCFCE7', fontSize: '13px', padding: '4px 10px' }}>
          ● Auto Completed
        </span>
      </div>

      {/* Summary bar */}
      <div className="stats-grid" style={{ marginBottom: '24px' }}>
        <StatCard icon={CheckCircle} label="Total Happy Path Cases" value={summary.total ?? 0} color="#16A34A" />
        <StatCard icon={TrendingUp} label="Auto Completed" value={summary.auto_completed ?? 0} color="#0D9488" />
        <StatCard icon={Clock} label="SLA Safe" value={summary.sla_safe ?? 0} color="#1E40AF" />
        <StatCard icon={AlertTriangle} label="At Risk" value={summary.at_risk ?? 0} color="#D97706" />
      </div>

      {/* Cases list */}
      {cases.length === 0 ? (
        <div className="empty-state">No happy path cases found. Run the pipeline to classify cases.</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {cases.map(c => {
            const ctx = c.context || {};
            const cls = c.classification || {};
            return (
              <div key={c.id} className="detail-card" style={{ borderLeft: '4px solid #16A34A' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '15px', marginBottom: '4px' }}>
                      {ctx.vendor || 'Unknown Vendor'}
                      <span style={{ fontWeight: 400, color: '#6B7280', marginLeft: '8px', fontSize: '13px' }}>
                        #{ctx.case_id}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', fontSize: '13px', color: '#374151' }}>
                      <span>Exposure: <strong>${(ctx.financial_exposure || 0).toLocaleString()}</strong></span>
                      <span>Confidence: <strong>{((cls.confidence || 0) * 100).toFixed(0)}%</strong></span>
                      <span>Team: <strong>{ctx.assigned_team || '—'}</strong></span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <Badge config={SLA_BADGE} value={c.sla_status || 'on_track'} />
                    <Badge config={RISK_BADGE} value={c.payment_risk_level || 'safe'} />
                    <Link
                      to={`/happy-path/${ctx.case_id || c.id}`}
                      className="btn btn-primary"
                      style={{ background: '#16A34A', color: '#fff', padding: '5px 12px', borderRadius: 4, fontSize: '13px', textDecoration: 'none' }}
                    >
                      View Details
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
