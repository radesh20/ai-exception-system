import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { AlertTriangle, BookOpen } from 'lucide-react';
import api from '../api';

const COLORS = ['#2563EB', '#0D9488', '#D97706', '#DC2626', '#7C3AED', '#6B7280'];

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
    <div className="page fade-in">
      {/* ── Header ── */}
      <div className="page-header">
        <div>
          <h1>Learning Insights</h1>
          <p className="page-subtitle">AI improves from every decision. Approve = reinforce. Reject = correct.</p>
        </div>
      </div>

      {/* ── KPI Section ── */}
      {insights && (
        <div className="section">
          <div className="kpi-grid">
            <KPI label="Total Decisions" value={insights.total_decisions} />
            <KPI label="Approval Rate" value={`${(insights.overall_approval_rate * 100).toFixed(0)}%`} />
            <KPI label="Policies Active" value={insights.policies_count} />
          </div>
        </div>
      )}

      {/* ── Chart Section ── */}
      {catData.length > 0 && (
        <div className="section">
          <div className="section-card">
            <div className="section-card-header">
              <h3>Approval Rate by Category</h3>
              <span className="section-meta">{catData.length} categories</span>
            </div>
            <div className="section-card-body">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={catData}>
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6B7280' }} axisLine={{ stroke: '#E2E6ED' }} tickLine={false} />
                  <YAxis unit="%" domain={[0, 100]} tick={{ fontSize: 11, fill: '#6B7280' }} axisLine={{ stroke: '#E2E6ED' }} tickLine={false} />
                  <Tooltip formatter={v => `${v}%`} contentStyle={{ background: '#FFFFFF', border: '1px solid #E2E6ED', borderRadius: '8px', fontSize: '12px' }} />
                  <Bar dataKey="rate" radius={[4, 4, 0, 0]}>
                    {catData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* ── Policy Performance Section ── */}
      <div className="section">
        <div className="section-card">
          <div className="section-card-header">
            <h3>Policy Performance</h3>
            <span className="section-meta">{policies.length} policies</span>
          </div>
          {policies.length > 0 ? (
            <div style={{ overflow: 'auto' }}>
              <table className="data-table" style={{ borderRadius: 0, border: 'none' }}>
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
                            background: (p.success_rate || 0) >= 80 ? '#0D9488' : '#D97706'
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
            </div>
          ) : (
            <div className="section-card-body">
              <div style={{ textAlign: 'center', padding: '24px', color: '#6B7280', fontSize: '13px' }}>
                <BookOpen size={20} style={{ marginBottom: '8px', opacity: 0.5 }} />
                <div>No policy data yet</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Attention Section ── */}
      {insights?.needs_attention?.length > 0 && (
        <div className="section">
          <div className="attention-box">
            <h3><AlertTriangle size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />Needs Attention</h3>
            {insights.needs_attention.map((item, i) => (
              <div key={i} className="attention-item">
                <strong>{item.category}</strong>: Low approval rate ({(item.approval_rate * 100).toFixed(0)}%, {item.sample_size} samples)
              </div>
            ))}
          </div>
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