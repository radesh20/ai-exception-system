import React, { useEffect, useState } from 'react';
import { ChevronDown, ChevronRight, ArrowDown, Clock } from 'lucide-react';
import api from '../api';

export default function AgentInteraction() {
  const [interactions, setInteractions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAgentInteractions()
      .then(d => {
        if (d && Array.isArray(d.interactions)) setInteractions(d.interactions);
      })
      .catch(() => { })
      .finally(() => setLoading(false));
  }, []);

  const handleSelect = (item) => {
    api.getAgentInteractionDetail(item.exception_id)
      .then(d => setSelected(d))
      .catch(() => { });
  };

  return (
    <div className="page fade-in">
      <div className="page-header">
        <div>
          <h1>Agent Interactions</h1>
          <p className="page-subtitle">
            Full prompt chain for each exception — see exactly what each agent received and produced.
          </p>
        </div>
      </div>

      <div className="stat-row">
        <div className="inline-stat">
          <span className="inline-stat-value">{interactions.length}</span>
          <span className="inline-stat-label">Traced exceptions</span>
        </div>
        {selected && (
          <div className="inline-stat">
            <span className="inline-stat-value">{selected.interactions?.[0]?.total_steps ?? selected.trace?.total_steps ?? '—'}</span>
            <span className="inline-stat-label">Agent steps</span>
          </div>
        )}
        {selected && (
          <div className="inline-stat">
            <span className="inline-stat-value">
              {selected.interactions?.[0]?.total_duration_ms ?? selected.trace?.total_duration_ms ?? '—'}ms
            </span>
            <span className="inline-stat-label">Total duration</span>
          </div>
        )}
      </div>

      <div className="analysis-layout">
        {/* Left: interaction list */}
        <div className="analysis-list">
          {loading && (
            <div style={{ padding: '24px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
              Loading...
            </div>
          )}
          {!loading && interactions.length === 0 && (
            <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
              <div>No agent interactions recorded yet.</div>
              <div style={{ marginTop: '8px' }}>Process an exception to see the full prompt chain.</div>
            </div>
          )}
          {interactions.map(item => (
            <div
              key={item.id || item.exception_id}
              className={`analysis-item${selected?.exception_id === item.exception_id ? ' active' : ''}`}
              onClick={() => handleSelect(item)}
            >
              <div className="ai-item-type" style={{ fontSize: '12px', fontWeight: 600 }}>
                {item.exception_id || 'Unknown'}
              </div>
              <div className="ai-item-meta">
                <span>{item.total_steps} steps</span>
                <span>{item.total_duration_ms}ms</span>
                <span style={{ color: 'var(--text-muted)' }}>
                  {item.recorded_at ? new Date(item.recorded_at).toLocaleDateString() : ''}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Right: interaction detail */}
        <div className="analysis-detail">
          {selected ? (
            <InteractionDetail data={selected} />
          ) : (
            <div className="empty-state" style={{ border: 'none' }}>
              <div className="empty-state-icon"><Clock size={20} /></div>
              <div className="empty-state-title">Select an interaction</div>
              <div className="empty-state-desc">
                Click an exception from the list to view the full agent prompt chain.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function InteractionDetail({ data }) {
  const steps = extractSteps(data);

  if (!steps || steps.length === 0) {
    return (
      <div style={{ padding: '24px', color: 'var(--text-muted)', fontSize: '13px' }}>
        No step details available for this interaction.
      </div>
    );
  }

  return (
    <div>
      <div className="detail-header">
        <h3>Exception: {data.exception_id}</h3>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          {steps.length} agent steps
        </span>
      </div>

      {steps.map((step, idx) => (
        <div key={idx}>
          <AgentStep step={step} index={idx} />
          {idx < steps.length - 1 && (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              padding: '4px 0', color: 'var(--text-muted)',
            }}>
              <ArrowDown size={16} />
              {step.output_used_as_input_by && (
                <span style={{ fontSize: '11px', marginLeft: '6px' }}>
                  → {step.output_used_as_input_by}
                </span>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function AgentStep({ step, index }) {
  const [promptOpen, setPromptOpen] = useState(false);
  const [responseOpen, setResponseOpen] = useState(false);

  const agentName = step.agent_name || step.agent || `Step ${index + 1}`;
  const prompt = step.prompt || step.input || '';
  const response = step.response || step.output || '';
  const durationMs = step.duration_ms || 0;
  const timestamp = step.timestamp || '';

  return (
    <div className="analysis-section" style={{ marginBottom: '8px' }}>
      {/* Step header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '22px', height: '22px', borderRadius: '50%',
            background: 'var(--primary)', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '11px', fontWeight: 700, flexShrink: 0,
          }}>
            {index + 1}
          </div>
          <h4 style={{ margin: 0, fontSize: '13px', fontWeight: 600 }}>{agentName}</h4>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {durationMs > 0 && (
            <span style={{
              fontSize: '11px', color: 'var(--text-muted)',
              background: 'var(--surface-2)', padding: '2px 6px', borderRadius: '4px',
            }}>
              {durationMs}ms
            </span>
          )}
          {timestamp && (
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              {new Date(timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Prompt block */}
      {prompt && (
        <div style={{ marginBottom: '6px' }}>
          <button
            onClick={() => setPromptOpen(o => !o)}
            style={{
              display: 'flex', alignItems: 'center', gap: '4px',
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-muted)', fontSize: '11px', padding: '0 0 4px 0',
            }}
          >
            {promptOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
            <span>Prompt sent in</span>
          </button>
          {promptOpen && (
            <div style={{
              background: 'var(--surface-2)', borderRadius: '6px',
              padding: '10px 12px', fontSize: '12px', fontFamily: 'monospace',
              whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              maxHeight: '280px', overflowY: 'auto',
              border: '1px solid var(--border)',
            }}>
              {prompt}
            </div>
          )}
        </div>
      )}

      {/* Response block */}
      {response && (
        <div>
          <button
            onClick={() => setResponseOpen(o => !o)}
            style={{
              display: 'flex', alignItems: 'center', gap: '4px',
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-muted)', fontSize: '11px', padding: '0 0 4px 0',
            }}
          >
            {responseOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
            <span>Response produced</span>
          </button>
          {responseOpen && (
            <div style={{
              background: '#f0fdf4', borderRadius: '6px',
              padding: '10px 12px', fontSize: '12px',
              whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              maxHeight: '280px', overflowY: 'auto',
              border: '1px solid #bbf7d0',
            }}>
              {response}
            </div>
          )}
          {!responseOpen && (
            <div style={{
              fontSize: '12px', color: 'var(--text-secondary)',
              fontStyle: 'italic', paddingLeft: '2px',
            }}>
              {String(response).slice(0, 120)}{String(response).length > 120 ? '…' : ''}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Normalise API response into a flat list of step objects regardless of
 * whether the data comes from the new AgentInteractionTracer or the legacy
 * AgentTracer stored in exception.recommended_action_params.agent_trace.
 */
function extractSteps(data) {
  if (!data) return [];

  // New tracer format
  if (data.interactions && Array.isArray(data.interactions)) {
    const first = data.interactions[0];
    if (first && Array.isArray(first.steps)) return first.steps;
  }

  // Legacy trace format
  if (data.trace && Array.isArray(data.trace.steps)) {
    return data.trace.steps;
  }

  // Direct steps array
  if (Array.isArray(data.steps)) return data.steps;

  return [];
}
