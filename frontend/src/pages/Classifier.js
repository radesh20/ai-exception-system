import React, { useEffect, useState } from 'react';
import { BarChart2, Star, Users, Zap } from 'lucide-react';
import api from '../api';
import ClassifierCharts from '../components/ClassifierCharts';

export default function Classifier() {
    const [exceptions, setExceptions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.getExceptions({ limit: 200 })
            .then(d => { if (Array.isArray(d)) setExceptions(d); })
            .catch(() => { })
            .finally(() => setLoading(false));
    }, []);

    const total = exceptions.length;
    const autoRouted = exceptions.filter(e => e.classification?.recommended_action !== 'escalate_to_human').length;
    const humanRouted = exceptions.filter(e => e.classification?.recommended_action === 'escalate_to_human').length;
    const novelCount = exceptions.filter(e => e.classification?.is_novel).length;
    const avgConf = total > 0
        ? (exceptions.reduce((s, e) => s + (e.classification?.confidence || 0), 0) / total * 100).toFixed(0)
        : 0;

    if (loading) return <div className="loading" />;

    return (
        <div className="page fade-in">

            {/* ── Header ── */}
            <div className="page-header">
                <div>
                    <h1>Classifier</h1>
                    <p className="page-subtitle">Exception type breakdown, routing distribution and confidence analysis</p>
                </div>
            </div>

            {/* ── KPI Row ── */}
            <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: '28px' }}>
                <KPI icon={<BarChart2 size={20} />} label="Classified Today" value={total} />
                <KPI icon={<Zap size={20} />} label="Auto-Routed" value={autoRouted} />
                <KPI icon={<Users size={20} />} label="Human-Routed" value={humanRouted} />
                <KPI icon={<Star size={20} />} label="Novel Exceptions" value={novelCount} alert={novelCount > 0} />
            </div>

            {/* ── Novel Banner ── */}
            {novelCount > 0 && (
                <div className="alert-banner" style={{
                    background: 'var(--purple-bg)',
                    borderColor: 'rgba(139,114,224,0.25)',
                    color: 'var(--purple-text)',
                    marginBottom: '24px'
                }}>
                    <Star size={15} />
                    <strong>{novelCount}</strong> novel exception{novelCount > 1 ? 's' : ''} detected — unseen patterns that may need rule updates.
                </div>
            )}

            {/* ── Charts ── */}
            <ClassifierCharts exceptions={exceptions} />

            {/* ── Confidence Scores Table ── */}
            <div className="section" style={{ marginTop: '12px' }}>
                <div className="section-header">
                    <span className="section-title">Confidence Scores</span>
                    <span className="section-meta">{total} records</span>
                </div>
                <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Case ID</th>
                                <th>Type</th>
                                <th>Vendor</th>
                                <th>Confidence</th>
                                <th>Routing</th>
                                <th>Novel</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {exceptions.length === 0 ? (
                                <tr>
                                    <td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '32px' }}>
                                        No exceptions found
                                    </td>
                                </tr>
                            ) : (
                                exceptions.slice(0, 50).map(exc => {
                                    const ctx = exc.context || {};
                                    const cls = exc.classification || {};
                                    const conf = ((cls.confidence || 0) * 100).toFixed(0);
                                    const isHuman = cls.recommended_action === 'escalate_to_human';
                                    const confColor = conf >= 80 ? 'var(--teal)' : conf >= 60 ? 'var(--amber)' : 'var(--red)';
                                    return (
                                        <tr key={exc.id}>
                                            <td><code className="mono">{exc.id?.slice(0, 13)}</code></td>
                                            <td style={{ textTransform: 'capitalize', fontWeight: 500 }}>
                                                {(ctx.exception_type || 'unknown').replace(/_/g, ' ')}
                                            </td>
                                            <td style={{ color: 'var(--text-muted)' }}>{ctx.vendor_id || '—'}</td>
                                            <td>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    <div style={{ width: '64px', height: '4px', background: 'var(--bg-elevated)', borderRadius: '2px', overflow: 'hidden' }}>
                                                        <div style={{ height: '100%', width: `${conf}%`, background: confColor, borderRadius: '2px' }} />
                                                    </div>
                                                    <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{conf}%</span>
                                                </div>
                                            </td>
                                            <td>
                                                <span className={`route-tag ${isHuman ? 'route-human' : 'route-auto'}`}>
                                                    {isHuman ? 'Human' : 'Auto'}
                                                </span>
                                            </td>
                                            <td>
                                                {cls.is_novel && <span className="badge badge-novel">Novel</span>}
                                            </td>
                                            <td>
                                                <a href={`/exception/${exc.id}`} className="card-link" style={{ fontSize: '12px' }}>
                                                    View →
                                                </a>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* ── Novel Exceptions Panel ── */}
            {novelCount > 0 && (
                <div className="section">
                    <div className="section-header">
                        <span className="section-title">Novel Exceptions</span>
                        <span className="section-meta">Confidence &lt; 60% · unseen patterns</span>
                    </div>
                    <div className="card-grid">
                        {exceptions
                            .filter(e => e.classification?.is_novel || (e.classification?.confidence || 0) < 0.6)
                            .slice(0, 6)
                            .map(exc => {
                                const ctx = exc.context || {};
                                const cls = exc.classification || {};
                                const conf = ((cls.confidence || 0) * 100).toFixed(0);
                                return (
                                    <div key={exc.id} className="exception-card priority-border-4">
                                        <div className="card-top">
                                            <div className="card-badges">
                                                <span className="badge badge-novel">Novel</span>
                                                <span className={`route-tag ${cls.recommended_action === 'escalate_to_human' ? 'route-human' : 'route-auto'}`}>
                                                    {cls.recommended_action === 'escalate_to_human' ? 'Human' : 'Auto'}
                                                </span>
                                            </div>
                                            <span className="card-id">{exc.id?.slice(0, 13)}</span>
                                        </div>
                                        <div className="card-type">{(ctx.exception_type || 'unknown').replace(/_/g, ' ')}</div>
                                        <div className="card-meta">
                                            <span>${(ctx.financial_exposure || 0).toLocaleString()}</span>
                                            <span>{ctx.vendor_id || '—'}</span>
                                            <span style={{ color: 'var(--red)' }}>P{cls.priority || '?'}</span>
                                        </div>
                                        {cls.hypothesis && (
                                            <div className="card-hypothesis">{cls.hypothesis}</div>
                                        )}
                                        <div className="card-footer">
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                <div style={{ width: '48px', height: '3px', background: 'var(--bg-elevated)', borderRadius: '2px', overflow: 'hidden' }}>
                                                    <div style={{ height: '100%', width: `${conf}%`, background: 'var(--red)', borderRadius: '2px' }} />
                                                </div>
                                                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{conf}%</span>
                                            </div>
                                            <a href={`/exception/${exc.id}`} className="card-link">View →</a>
                                        </div>
                                    </div>
                                );
                            })}
                    </div>
                </div>
            )}
        </div>
    );
}

function KPI({ icon, label, value, alert }) {
    return (
        <div className={`kpi-card${alert ? ' kpi-alert' : ''}`}>
            <div className="kpi-icon">{icon}</div>
            <div className="kpi-value">{value}</div>
            <div className="kpi-label">{label}</div>
        </div>
    );
}