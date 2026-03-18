import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api';
import { PriorityBadge } from '../components/StatusBadge';
import DecisionForm from '../components/DecisionForm';

export default function PendingDecisions({ onDecision }) {
  const [pending, setPending] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchParams] = useSearchParams();
  const targetId = searchParams.get('exception_id');

  const load = () => {
    api.getPending().then(data => {
      const list = Array.isArray(data) ? data : [];
      setPending(list);
      if (targetId) {
        const found = list.find(e => e.id === targetId);
        if (found) setSelected(found);
      } else if (list.length > 0 && !selected) {
        setSelected(list[0]);
      }
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleDecision = () => {
    if (onDecision) onDecision();
    setSelected(null);
    load();
  };

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>;

  return (
    <div className="page">
      <h1>👤 Pending Decisions</h1>

      {pending.length === 0 ? (
        <div className="success-state">
          <div className="success-icon">✅</div>
          <h2>All Caught Up!</h2>
          <p>No exceptions waiting for human review.</p>
        </div>
      ) : (
        <div className="decisions-layout">
          <div className="decisions-queue">
            <div className="queue-header">
              <h3>Review Queue</h3>
              <span className="queue-count">{pending.length}</span>
            </div>
            {pending.map(exc => {
              const ctx = exc.context || {};
              const cls = exc.classification || {};
              return (
                <div key={exc.id}
                  className={`queue-item${selected?.id === exc.id ? ' active' : ''}`}
                  onClick={() => setSelected(exc)}>
                  <div className="queue-item-type">
                    {(ctx.exception_type || 'unknown').replace(/_/g, ' ')}
                  </div>
                  <div className="queue-item-meta">
                    <span>P{cls.priority || '?'}</span>
                    <span>${(ctx.financial_exposure || 0).toLocaleString()}</span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="decisions-detail">
            {selected ? (
              <>
                <div className="decision-summary">
                  <h3>Exception Details</h3>
                  <div className="summary-grid">
                    <Field label="Type" value={(selected.context?.exception_type || '').replace(/_/g, ' ')} />
                    <Field label="Exposure" value={`$${(selected.context?.financial_exposure || 0).toLocaleString()}`} />
                    <Field label="Team" value={selected.context?.assigned_team} />
                    <Field label="Vendor" value={selected.context?.vendor} />
                    <Field label="Severity" value={selected.context?.severity_score?.toFixed(2)} />
                    <Field label="Compliance" value={selected.context?.compliance_flag ? '⚠️ Flagged' : 'Clean'} />
                  </div>

                  <h4>Process Path</h4>
                  <PathDisplay
                    actual={selected.context?.actual_path || []}
                    happy={selected.context?.happy_path || []}
                    deviation={selected.context?.deviation_point}
                  />

                  <h4>🤖 AI Root Cause</h4>
                  <div className="hypothesis-box">
                    {selected.root_cause?.hypothesis || 'Analysis pending'}
                  </div>
                  <p style={{fontSize:'12px',color:'#666',marginTop:'4px'}}>
                    Confidence: {((selected.root_cause?.confidence || 0) * 100).toFixed(0)}%
                    {selected.root_cause?.supporting_cases?.length > 0 && (
                      <> | Supporting cases: {selected.root_cause.supporting_cases.join(', ')}</>
                    )}
                  </p>
                </div>

                <DecisionForm exception={selected} onComplete={handleDecision} />
              </>
            ) : (
              <div className="empty-state">← Select an exception from the queue</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div className="field">
      <span className="field-label">{label}:</span>
      <span className="field-value">{value || '—'}</span>
    </div>
  );
}

function PathDisplay({ actual, happy, deviation }) {
  return (
    <div className="path-display">
      <div className="path-row">
        <span className="path-label">Actual:</span>
        <div className="path-steps">
          {actual.map((step, i) => (
            <React.Fragment key={i}>
              <span className={`step${step === deviation ? ' step-deviation' : ''}`}>{step}</span>
              {i < actual.length - 1 && <span className="step-arrow">→</span>}
            </React.Fragment>
          ))}
        </div>
      </div>
      <div className="path-row">
        <span className="path-label">Happy:</span>
        <div className="path-steps">
          {happy.map((step, i) => (
            <React.Fragment key={i}>
              <span className="step step-happy">{step}</span>
              {i < happy.length - 1 && <span className="step-arrow">→</span>}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}