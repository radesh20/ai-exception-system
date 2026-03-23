import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle, Clock } from 'lucide-react';
import api from '../api';

/* ── Badge helpers ──────────────────────────────────────────────────────── */

function TypeBadge({ type }) {
  const cfg = {
    'Happy Path': { color: '#065F46', bg: '#DCFCE7' },
    'Exception':  { color: '#991B1B', bg: '#FEE2E2' },
    'Shared':     { color: '#1E40AF', bg: '#DBEAFE' },
  }[type] || { color: '#374151', bg: '#F1F3F7' };
  return <span className="badge" style={cfg}>{type}</span>;
}

function StatusBadge({ status }) {
  const cfg = {
    'Built':   { color: '#065F46', bg: '#DCFCE7' },
    'Planned': { color: '#6B7280', bg: '#F1F3F7' },
    'Ran':     { color: '#065F46', bg: '#D1FAE5' },
    'Skipped': { color: '#6B7280', bg: '#F3F4F6' },
  }[status] || { color: '#374151', bg: '#F1F3F7' };
  return <span className="badge" style={cfg}>{status}</span>;
}

/* ── Flowchart ──────────────────────────────────────────────────────────── */

function Flowchart({ stages, highlightAgents = [] }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0', overflowX: 'auto', padding: '16px 0' }}>
      {stages.map((s, i) => {
        const ran = highlightAgents.length > 0 &&
          (highlightAgents.some(a => s.agent.includes(a)) || ['ContextBuilderAgent', 'PathClassifier'].includes(s.agent));
        return (
          <React.Fragment key={i}>
            <div style={{
              padding: '10px 14px',
              borderRadius: 6,
              border: `2px solid ${ran ? '#16A34A' : '#D1D5DB'}`,
              background: ran ? '#DCFCE7' : '#F9FAFB',
              minWidth: '120px',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: ran ? '#065F46' : '#374151' }}>{s.stage}</div>
              <div style={{ fontSize: '11px', color: '#6B7280', marginTop: '2px' }}>{s.agent}</div>
              <TypeBadge type={s.type} />
            </div>
            {i < stages.length - 1 && (
              <div style={{ color: '#9CA3AF', fontSize: '18px', padding: '0 4px' }}>→</div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

/* ── Agent card ─────────────────────────────────────────────────────────── */

function AgentCard({ agent, ran, caseResult }) {
  const [open, setOpen] = useState(false);
  const isBuilt = agent.status === 'Built';
  const accentColor = agent.type === 'Happy Path' ? '#16A34A' : agent.type === 'Exception' ? '#DC2626' : '#1E40AF';

  return (
    <div className="detail-card" style={{ borderTop: `3px solid ${accentColor}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
        <div>
          <span style={{ fontWeight: 600, fontSize: '15px' }}>{agent.agent_name}</span>
          <div style={{ display: 'flex', gap: '6px', marginTop: '4px', flexWrap: 'wrap' }}>
            <TypeBadge type={agent.type} />
            {ran !== undefined ? (
              <StatusBadge status={ran ? 'Ran' : 'Skipped'} />
            ) : (
              <StatusBadge status={agent.status || 'Built'} />
            )}
          </div>
        </div>
        <button
          onClick={() => setOpen(p => !p)}
          style={{ background: 'none', border: '1px solid #D1D5DB', padding: '4px 10px', borderRadius: 4, cursor: 'pointer', fontSize: '12px' }}
        >
          {open ? 'collapse ▴' : 'details ▾'}
        </button>
      </div>

      <p style={{ fontSize: '13px', color: '#374151', margin: '0 0 4px' }}>{agent.function}</p>

      {agent.data_justification && (
        <p style={{ fontSize: '12px', color: '#6B7280', margin: 0 }}>{agent.data_justification}</p>
      )}

      {open && (
        <div style={{ marginTop: '12px', borderTop: '1px solid #F3F4F6', paddingTop: '12px' }}>
          {agent.inputs && (
            <div style={{ fontSize: '12px', marginBottom: '6px' }}>
              <strong>Inputs:</strong> {agent.inputs.join(', ')}
            </div>
          )}
          {agent.outputs && (
            <div style={{ fontSize: '12px', marginBottom: '6px' }}>
              <strong>Outputs:</strong> {agent.outputs.join(', ')}
            </div>
          )}
          {agent.process_stage && (
            <div style={{ fontSize: '12px' }}>
              <strong>Stage:</strong> {agent.process_stage}
            </div>
          )}
          {caseResult && (
            <div style={{ marginTop: '10px', background: '#F9FAFB', borderRadius: 4, padding: '8px', fontSize: '12px' }}>
              <strong>Case Output:</strong>
              <pre style={{ margin: '4px 0 0', overflow: 'auto', maxHeight: '120px' }}>
                {JSON.stringify(caseResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Reference table ────────────────────────────────────────────────────── */

function ReferenceTable({ agents, agentsRan }) {
  return (
    <div className="detail-card" style={{ padding: 0, overflow: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ background: '#F9FAFB', borderBottom: '1px solid #E5E7EB' }}>
            {['Agent Name', 'Process Stage', 'Type', 'Status'].map(h => (
              <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 600, color: '#374151' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {agents.map((a, i) => {
            const ran = agentsRan ? agentsRan.includes(a.agent_name) : undefined;
            return (
              <tr key={i} style={{ borderBottom: '1px solid #F3F4F6' }}>
                <td style={{ padding: '8px 12px', fontWeight: 500 }}>{a.agent_name}</td>
                <td style={{ padding: '8px 12px', color: '#6B7280' }}>{a.process_stage || '—'}</td>
                <td style={{ padding: '8px 12px' }}><TypeBadge type={a.type || 'Shared'} /></td>
                <td style={{ padding: '8px 12px' }}>
                  {ran !== undefined ? (
                    <StatusBadge status={ran ? 'Ran' : 'Skipped'} />
                  ) : (
                    <StatusBadge status={a.status || 'Built'} />
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* ── Main component ─────────────────────────────────────────────────────── */

export default function ProcessAgents() {
  const { caseId } = useParams();
  const isPerCase = !!caseId;

  const [globalData, setGlobalData] = useState(null);
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetches = [api.getProcessAgents().then(d => { if (d) setGlobalData(d); })];
    if (isPerCase) {
      fetches.push(api.getProcessAgentsByCase(caseId).then(d => { if (d && !d.error) setCaseData(d); }));
    }
    Promise.all(fetches).catch(() => {}).finally(() => setLoading(false));
  }, [caseId]);

  if (loading) return <div className="page fade-in"><div className="loading">Loading process agents…</div></div>;

  const flowchart = globalData?.flowchart || [];
  const allAgents = globalData?.agents || [];
  const agentsRan = caseData?.agents_ran || null;
  const caseResults = caseData?.results || {};

  // Merged agent list: for per-case view enrich with case results
  const displayAgents = allAgents.map(a => ({
    ...a,
    _caseResult: caseResults[
      a.agent_name === 'PaymentRiskAgent' ? 'payment_risk' :
      a.agent_name === 'SLAMonitorAgent' ? 'sla_monitor' :
      a.agent_name === 'ProcessOptimizationAgent' ? 'process_optimization' : null
    ] || null,
  }));

  return (
    <div className="page fade-in">
      <div className="page-header">
        <div>
          {isPerCase && (
            <Link to={`/happy-path/${caseId}`} className="back-link"><ArrowLeft size={14} /> Back to Case</Link>
          )}
          <h1>{isPerCase ? `Process Agents — Case #${caseId}` : 'Process Agents'}</h1>
          <p className="page-subtitle">
            {isPerCase
              ? `Agents that ran for case ${caseId} are highlighted in green.`
              : 'All available process agents for the P2P pipeline.'}
          </p>
        </div>
        {isPerCase && caseData && (
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <span className="badge" style={{ color: '#065F46', background: '#DCFCE7' }}>
              <CheckCircle size={12} style={{ marginRight: 4 }} />
              {agentsRan?.length || 0} Ran
            </span>
            <span className="badge" style={{ color: '#6B7280', background: '#F1F3F7' }}>
              <Clock size={12} style={{ marginRight: 4 }} />
              {(caseData.agents_skipped || []).length} Skipped
            </span>
          </div>
        )}
      </div>

      {/* Flowchart */}
      <div className="detail-card" style={{ marginBottom: '16px' }}>
        <h3 style={{ marginBottom: '8px' }}>Pipeline Flowchart</h3>
        <Flowchart stages={flowchart} highlightAgents={agentsRan || []} />
      </div>

      {/* Agent cards grid */}
      <div className="stats-grid" style={{ marginBottom: '16px' }}>
        {displayAgents.map((a, i) => (
          <AgentCard
            key={i}
            agent={a}
            ran={agentsRan ? agentsRan.includes(a.agent_name) : undefined}
            caseResult={a._caseResult}
          />
        ))}
      </div>

      {/* Reference table */}
      <h3 style={{ marginBottom: '10px' }}>Agent Reference Table</h3>
      <ReferenceTable agents={allAgents} agentsRan={agentsRan} />
    </div>
  );
}
