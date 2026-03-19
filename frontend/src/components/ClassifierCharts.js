import React, { useMemo } from 'react';
import {
    PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
    BarChart, Bar, XAxis, YAxis, CartesianGrid,
    RadialBarChart, RadialBar
} from 'recharts';

const COLORS = {
    teal: '#0D9488',
    violet: '#7C3AED',
    amber: '#D97706',
    blue: '#2563EB',
    rose: '#E11D48',
    sky: '#0EA5E9',
    green: '#16A34A',
    orange: '#EA580C',
};

const PALETTE = Object.values(COLORS);

const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
        <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: '8px', padding: '10px 14px', fontSize: '12px',
            boxShadow: 'var(--shadow-md)'
        }}>
            {label && <div style={{ color: 'var(--text-muted)', marginBottom: '4px' }}>{label}</div>}
            {payload.map((p, i) => (
                <div key={i} style={{ color: 'var(--text-heading)', display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: p.fill || p.color, display: 'inline-block' }} />
                    {p.name}: <strong>{p.value}</strong>
                </div>
            ))}
        </div>
    );
};

export default function ClassifierCharts({ exceptions }) {

    // ── 1. Exception Type Breakdown (Pie) ──
    const typeData = useMemo(() => {
        const counts = {};
        exceptions.forEach(e => {
            const t = (e.context?.exception_type || 'unknown').replace(/_/g, ' ');
            counts[t] = (counts[t] || 0) + 1;
        });
        return Object.entries(counts)
            .sort((a, b) => b[1] - a[1])
            .map(([name, value]) => ({ name, value }));
    }, [exceptions]);

    // ── 2. Routing Distribution (Donut) ──
    const routingData = useMemo(() => {
        const auto = exceptions.filter(e => e.classification?.recommended_action !== 'escalate_to_human').length;
        const human = exceptions.filter(e => e.classification?.recommended_action === 'escalate_to_human').length;
        return [
            { name: 'Auto-Routed', value: auto },
            { name: 'Human-Routed', value: human },
        ];
    }, [exceptions]);

    // ── 3. Vendor-wise Exceptions (Horizontal Bar) ──
    const vendorData = useMemo(() => {
        const counts = {};
        exceptions.forEach(e => {
            const v = e.context?.vendor_id || 'Unknown';
            counts[v] = (counts[v] || 0) + 1;
        });
        return Object.entries(counts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8)
            .map(([name, value]) => ({ name, value }));
    }, [exceptions]);

    // ── 4. Confidence Distribution (Bar) ──
    const confData = useMemo(() => {
        const buckets = { '0–40%': 0, '40–60%': 0, '60–80%': 0, '80–100%': 0 };
        exceptions.forEach(e => {
            const c = (e.classification?.confidence || 0) * 100;
            if (c < 40) buckets['0–40%']++;
            else if (c < 60) buckets['40–60%']++;
            else if (c < 80) buckets['60–80%']++;
            else buckets['80–100%']++;
        });
        return Object.entries(buckets).map(([name, value]) => ({ name, value }));
    }, [exceptions]);

    const confColors = [COLORS.rose, COLORS.amber, COLORS.sky, COLORS.teal];

    return (
        <div>
            {/* ── Row 1: Pie + Donut ── */}
            <div className="dashboard-two-col" style={{ marginBottom: '16px' }}>

                {/* Exception Type Breakdown */}
                <div className="section-card">
                    <div className="section-card-header">
                        <h3>Exception Type Breakdown</h3>
                        <span className="section-meta">{typeData.length} types</span>
                    </div>
                    <div className="section-card-body">
                        {typeData.length === 0 ? (
                            <EmptyChart />
                        ) : (
                            <ResponsiveContainer width="100%" height={260}>
                                <PieChart>
                                    <Pie
                                        data={typeData}
                                        cx="50%" cy="50%"
                                        outerRadius={90}
                                        dataKey="value"
                                        labelLine={false}
                                        label={({ name, percent }) =>
                                            percent > 0.07 ? `${(percent * 100).toFixed(0)}%` : ''
                                        }
                                    >
                                        {typeData.map((_, i) => (
                                            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip content={<CustomTooltip />} />
                                    <Legend
                                        iconType="circle" iconSize={8}
                                        formatter={v => <span style={{ fontSize: '11px', color: 'var(--text-body)' }}>{v}</span>}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>

                {/* Routing Distribution */}
                <div className="section-card">
                    <div className="section-card-header">
                        <h3>Routing Distribution</h3>
                        <span className="section-meta">Auto vs Human</span>
                    </div>
                    <div className="section-card-body">
                        {routingData.every(d => d.value === 0) ? (
                            <EmptyChart />
                        ) : (
                            <>
                                <ResponsiveContainer width="100%" height={220}>
                                    <PieChart>
                                        <Pie
                                            data={routingData}
                                            cx="50%" cy="50%"
                                            innerRadius={60} outerRadius={90}
                                            dataKey="value"
                                            paddingAngle={3}
                                        >
                                            <Cell fill={COLORS.teal} />
                                            <Cell fill={COLORS.rose} />
                                        </Pie>
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend
                                            iconType="circle" iconSize={8}
                                            formatter={v => <span style={{ fontSize: '11px', color: 'var(--text-body)' }}>{v}</span>}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                                {/* Center stats */}
                                <div style={{ display: 'flex', justifyContent: 'center', gap: '32px', marginTop: '8px' }}>
                                    {routingData.map((d, i) => (
                                        <div key={i} style={{ textAlign: 'center' }}>
                                            <div style={{ fontSize: '20px', fontWeight: 700, color: i === 0 ? COLORS.teal : COLORS.rose, letterSpacing: '-0.02em' }}>
                                                {exceptions.length > 0 ? ((d.value / exceptions.length) * 100).toFixed(0) : 0}%
                                            </div>
                                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{d.name}</div>
                                        </div>
                                    ))}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>

            {/* ── Row 2: Vendor Bar + Confidence Bar ── */}
            <div className="dashboard-two-col">

                {/* Vendor-wise Exceptions */}
                <div className="section-card">
                    <div className="section-card-header">
                        <h3>Vendor-wise Exceptions</h3>
                        <span className="section-meta">Top {vendorData.length}</span>
                    </div>
                    <div className="section-card-body">
                        {vendorData.length === 0 ? (
                            <EmptyChart />
                        ) : (
                            <ResponsiveContainer width="100%" height={260}>
                                <BarChart
                                    data={vendorData}
                                    layout="vertical"
                                    margin={{ left: 8, right: 24, top: 4, bottom: 4 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                                    <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                                    <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} width={90} />
                                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--bg-hover)' }} />
                                    <Bar dataKey="value" name="Exceptions" radius={[0, 4, 4, 0]}>
                                        {vendorData.map((_, i) => (
                                            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>

                {/* Confidence Distribution */}
                <div className="section-card">
                    <div className="section-card-header">
                        <h3>Confidence Distribution</h3>
                        <span className="section-meta">By bucket</span>
                    </div>
                    <div className="section-card-body">
                        {exceptions.length === 0 ? (
                            <EmptyChart />
                        ) : (
                            <ResponsiveContainer width="100%" height={260}>
                                <BarChart
                                    data={confData}
                                    margin={{ left: 0, right: 16, top: 4, bottom: 4 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                                    <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--bg-hover)' }} />
                                    <Bar dataKey="value" name="Count" radius={[4, 4, 0, 0]}>
                                        {confData.map((_, i) => (
                                            <Cell key={i} fill={confColors[i]} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function EmptyChart() {
    return (
        <div style={{ height: '260px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
            No data yet
        </div>
    );
}