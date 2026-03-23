import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

/* ── Badge helpers ──────────────────────────────────────────────────────── */

const URGENCY_CFG = {
  immediate: { label: 'Immediate', color: '#991B1B', bg: '#FEE2E2' },
  today:     { label: 'Today',     color: '#92400E', bg: '#FEF3C7' },
  critical:  { label: 'Critical',  color: '#991B1B', bg: '#FEE2E2' },
  at_risk:   { label: 'At Risk',   color: '#92400E', bg: '#FEF3C7' },
  this_week: { label: 'This Week', color: '#1E40AF', bg: '#DBEAFE' },
  on_track:  { label: 'On Track',  color: '#065F46', bg: '#DCFCE7' },
  safe:      { label: 'Safe',      color: '#065F46', bg: '#DCFCE7' },
};

function UrgencyBadge({ level }) {
  const cfg = URGENCY_CFG[level] || { label: level, color: '#374151', bg: '#F1F3F7' };
  return <span className="badge" style={{ color: cfg.color, background: cfg.bg }}>{cfg.label}</span>;
}

/* ── Derive urgency from an insight record ──────────────────────────────── */

function getUrgency(record) {
  const pr = (record.payment_risk || {}).risk_level || 'safe';
  const sla = (record.sla_monitor || {}).status || 'on_track';
  const order = { immediate: 0, today: 1, critical: 2, at_risk: 3, this_week: 4, safe: 5, on_track: 6 };
  return order[pr] <= order[sla] ? pr : sla;
}

function isAlert(record) {
  const pr = (record.payment_risk || {}).risk_level || 'safe';
  const sla = (record.sla_monitor || {}).status || 'on_track';
  return ['immediate', 'today'].includes(pr) || ['critical', 'at_risk'].includes(sla);
}

/* ── Alert card ─────────────────────────────────────────────────────────── */

function AlertCard({ record }) {
  const urgency = getUrgency(record);
  const pr = record.payment_risk || {};
  const sla = record.sla_monitor || {};
  const opt = record.process_optimization || {};
  const caseId = record.case_id || '';

  const primaryInsight = pr.insight || sla.insight || opt.insight || 'No insight available.';
  const primaryAction = pr.recommended_action || sla.recommended_action || opt.recommended_action || '';

  return (
    <div className="detail-card" style={{ borderLeft: `4px solid ${URGENCY_CFG[urgency]?.bg === '#FEE2E2' ? '#DC2626' : '#D97706'}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
            <UrgencyBadge level={urgency} />
            <span style={{ fontWeight: 600 }}>{record.vendor || 'Unknown Vendor'}</span>
            <span style={{ color: '#6B7280', fontSize: '13px' }}>#{caseId}</span>
          </div>
          <div style={{ fontSize: '14px', marginBottom: '4px' }}>{primaryInsight}</div>
          {primaryAction && (
            <div style={{ fontSize: '13px', color: '#374151', padding: '4px 8px', background: '#F9FAFB', borderRadius: 4 }}>
              → {primaryAction}
            </div>
          )}
        </div>
        <Link
          to={`/happy-path/${caseId}`}
          className="btn"
          style={{ background: '#16A34A', color: '#fff', padding: '5px 12px', borderRadius: 4, fontSize: '13px', textDecoration: 'none', alignSelf: 'flex-start', whiteSpace: 'nowrap' }}
        >
          View Case
        </Link>
      </div>
    </div>
  );
}

/* ── Main component ─────────────────────────────────────────────────────── */

export default function ProcessInsights() {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filter/search state
  const [search, setSearch] = useState('');
  const [filterVendor, setFilterVendor] = useState('');
  const [filterUrgency, setFilterUrgency] = useState('');
  const [filterType, setFilterType] = useState('');

  useEffect(() => {
    api.getProcessInsights()
      .then(d => { if (Array.isArray(d)) setInsights(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page fade-in"><div className="loading">Loading process insights…</div></div>;

  const alerts = insights.filter(isAlert).sort((a, b) => {
    const order = { immediate: 0, today: 1, critical: 2, at_risk: 3 };
    return (order[getUrgency(a)] ?? 9) - (order[getUrgency(b)] ?? 9);
  });

  const vendors = [...new Set(insights.map(r => r.vendor).filter(Boolean))];

  // Build flat rows for the table
  const tableRows = [];
  for (const rec of insights) {
    const caseId = rec.case_id || '';
    const vendor = rec.vendor || '';
    if (rec.payment_risk?.insight) {
      tableRows.push({ caseId, vendor, type: 'Payment Risk', urgency: (rec.payment_risk.risk_level || 'safe'), insight: rec.payment_risk.insight, action: rec.payment_risk.recommended_action });
    }
    if (rec.sla_monitor?.insight) {
      tableRows.push({ caseId, vendor, type: 'SLA Monitor', urgency: (rec.sla_monitor.status || 'on_track'), insight: rec.sla_monitor.insight, action: rec.sla_monitor.recommended_action });
    }
    if (rec.process_optimization?.insight) {
      tableRows.push({ caseId, vendor, type: 'Optimization', urgency: rec.process_optimization.delay_days > 2 ? 'at_risk' : 'safe', insight: rec.process_optimization.insight, action: rec.process_optimization.recommended_action });
    }
  }

  const filtered = tableRows.filter(r => {
    if (search && !r.caseId.toLowerCase().includes(search.toLowerCase()) && !r.vendor.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterVendor && r.vendor !== filterVendor) return false;
    if (filterUrgency && r.urgency !== filterUrgency) return false;
    if (filterType && r.type !== filterType) return false;
    return true;
  });

  return (
    <div className="page fade-in">
      <div className="page-header">
        <div>
          <h1>Process Insights</h1>
          <p className="page-subtitle">Payment risk, SLA monitoring, and process optimisation alerts</p>
        </div>
        {alerts.length > 0 && (
          <span className="badge" style={{ color: '#991B1B', background: '#FEE2E2', fontSize: '13px', padding: '4px 10px' }}>
            {alerts.length} Alert{alerts.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Alert cards */}
      {alerts.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ marginBottom: '12px', color: '#DC2626' }}>⚠ Active Alerts</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {alerts.map(r => <AlertCard key={r.case_id} record={r} />)}
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '16px' }}>
        <input
          type="text"
          placeholder="Search by case ID or vendor…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ padding: '6px 10px', borderRadius: 4, border: '1px solid #D1D5DB', fontSize: '13px', flex: '1 1 200px' }}
        />
        <select value={filterVendor} onChange={e => setFilterVendor(e.target.value)}
          style={{ padding: '6px 10px', borderRadius: 4, border: '1px solid #D1D5DB', fontSize: '13px' }}>
          <option value="">All Vendors</option>
          {vendors.map(v => <option key={v} value={v}>{v}</option>)}
        </select>
        <select value={filterUrgency} onChange={e => setFilterUrgency(e.target.value)}
          style={{ padding: '6px 10px', borderRadius: 4, border: '1px solid #D1D5DB', fontSize: '13px' }}>
          <option value="">All Urgency</option>
          {Object.keys(URGENCY_CFG).map(u => <option key={u} value={u}>{URGENCY_CFG[u].label}</option>)}
        </select>
        <select value={filterType} onChange={e => setFilterType(e.target.value)}
          style={{ padding: '6px 10px', borderRadius: 4, border: '1px solid #D1D5DB', fontSize: '13px' }}>
          <option value="">All Types</option>
          <option value="Payment Risk">Payment Risk</option>
          <option value="SLA Monitor">SLA Monitor</option>
          <option value="Optimization">Optimization</option>
        </select>
      </div>

      {/* Table */}
      <div className="detail-card" style={{ padding: 0, overflow: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#F9FAFB', borderBottom: '1px solid #E5E7EB' }}>
              {['Case ID', 'Vendor', 'Type', 'Urgency', 'Insight', 'Recommended Action'].map(h => (
                <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 600, color: '#374151', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr><td colSpan={6} style={{ padding: '24px', textAlign: 'center', color: '#6B7280' }}>No insights match the current filters.</td></tr>
            ) : filtered.map((r, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #F3F4F6' }}>
                <td style={{ padding: '8px 12px' }}>
                  <Link to={`/happy-path/${r.caseId}`} style={{ color: '#16A34A', textDecoration: 'none' }}>{r.caseId}</Link>
                </td>
                <td style={{ padding: '8px 12px' }}>{r.vendor}</td>
                <td style={{ padding: '8px 12px' }}>{r.type}</td>
                <td style={{ padding: '8px 12px' }}><UrgencyBadge level={r.urgency} /></td>
                <td style={{ padding: '8px 12px', maxWidth: '300px' }}>{r.insight}</td>
                <td style={{ padding: '8px 12px', maxWidth: '220px', color: '#374151' }}>{r.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
