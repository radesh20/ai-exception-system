import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import api from '../api';

const COLORS = ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#0dcaf0', '#6c757d'];

export default function LearningInsights() {
  const [insights, setInsights] = useState(null);
  const [policies, setPolicies] = useState([]);

  useEffect(() => {
    api.getLearning().then(d => { if (d) setInsights(d); }).catch(() => {});
    api.getPolicyPerf().then(d => { if (Array.isArray(d)) setPolicies(d); }).catch(() => {});
  }, []);

  const catData = insights
    ? Object.entries(insights.by_category || {}).map(([cat, s]) => ({
        name: cat.replace(/_/g, ' '),
        approved: s.approved || 0,
        rejected: s.rejected || 0,
        rate: s.total > 0 ? Math.round((s.approved / s.total) * 100) : 0,
      }))
    : [];

  return (
    <div className="page">
      <h1>📈 Learning Insights</h1>
      <p className="page-desc">AI improves from every decision. Approve = reinforce. Reject = correct.</p>

      {insights && (
        <div className="kpi-grid">
          <KPI label="Total Decisions" value={insights.total_decisions} />
          <KPI label="Approval Rate" value={`${(insights.overall_approval_rate * 100).toFixed(0)}%`} />
          <KPI label="Policies Active" value={insights.policies_count} />
        </div>
      )}

      {catData.length > 0 && (
        <div className="chart-card">
          <h2>Approval Rate by Category</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={catData}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis unit="%" domain={[0, 100]} />
              <Tooltip formatter={v => `${v}%`} />
              <Bar dataKey="rate" radius={[4, 4, 0, 0]}>
                {catData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <h2>Policy Performance</h2>
      {policies.length > 0 ? (
        <table className="data-table">
          <thead><tr><th>Category</th><th>Action</th><th>Success</th><th>Samples</th><th>Confidence</th></tr></thead>
          <tbody>
            {policies.map((p, i) => (
              <tr key={i}>
                <td>{(p.category || '').replace(/_/g, ' ')}</td>
                <td><code>{p.action_type}</code></td>
                <td>
                  <div className="mini-bar">
                    <div><div className="mini-fill" style={{
                      width: `${p.success_rate || 0}%`,
                      background: (p.success_rate || 0) >= 80 ? '#198754' : '#ffc107'
                    }} /></div>
                    <span>{p.success_rate || 0}%</span>
                  </div>
                </td>
                <td>{p.sample_size}</td>
                <td><span className={`conf-tag conf-${p.confidence}`}>{p.confidence}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="empty-state">No policy data yet.</div>
      )}

      {insights?.needs_attention?.length > 0 && (
        <div className="attention-box">
          <h3>⚠️ Needs Attention</h3>
          {insights.needs_attention.map((item, i) => (
            <div key={i} className="attention-item">
              <strong>{item.category}</strong>: Low approval rate ({(item.approval_rate * 100).toFixed(0)}%, {item.sample_size} samples)
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function KPI({ label, value }) {
  return (
    <div className="kpi-card">
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  );
}