import React, { useState } from 'react';
import api from '../api';

export default function DecisionForm({ exception, onComplete }) {
  const [type, setType] = useState('approved');
  const [analyst, setAnalyst] = useState('');
  const [notes, setNotes] = useState('');
  const [customAction, setCustomAction] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!analyst.trim()) { setError('Please enter your name'); return; }
    setLoading(true);
    setError('');
    try {
      await api.submitDecision({
        exception_id: exception.id,
        decision_type: type,
        analyst_name: analyst,
        notes,
        final_action: type === 'modified' ? customAction : exception.recommended_action,
      });
      if (onComplete) onComplete();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="decision-form">
      <h3>📋 Your Decision</h3>

      {/* AI Recommendation */}
      <div className="ai-rec">
        <span className="ai-rec-label">🤖 AI Recommends:</span>
        <strong>{exception.recommended_action || 'escalate_to_human'}</strong>
        <span className="ai-confidence">
          ({((exception.classification?.confidence || 0) * 100).toFixed(0)}% confidence)
        </span>
      </div>

      {/* AI Reasoning */}
      {exception.ai_reasoning && (
        <div className="reasoning-box">
          <strong>AI Reasoning:</strong> {exception.ai_reasoning}
        </div>
      )}

      {/* Decision Options */}
      <div className="form-group">
        <label>Decision</label>
        <div className="radio-row">
          {[
            { val: 'approved',   icon: '✅', label: 'Approve' },
            { val: 'rejected',   icon: '❌', label: 'Reject' },
            { val: 'modified',   icon: '✏️', label: 'Modify' },
            { val: 'escalated',  icon: '⬆️', label: 'Escalate' },
          ].map(({ val, icon, label }) => (
            <label key={val} className={`radio-btn${type === val ? ' selected' : ''}`}>
              <input type="radio" value={val} checked={type === val}
                     onChange={() => setType(val)} />
              {icon} {label}
            </label>
          ))}
        </div>
      </div>

      {/* Custom action if modified */}
      {type === 'modified' && (
        <div className="form-group">
          <label>Custom Action</label>
          <input type="text" value={customAction}
                 onChange={e => setCustomAction(e.target.value)}
                 placeholder="e.g., manual_review" />
        </div>
      )}

      {/* Analyst Name */}
      <div className="form-group">
        <label>Your Name *</label>
        <input type="text" value={analyst}
               onChange={e => setAnalyst(e.target.value)}
               placeholder="e.g., jane.doe" />
      </div>

      {/* Notes */}
      <div className="form-group">
        <label>Notes</label>
        <textarea value={notes} onChange={e => setNotes(e.target.value)}
                  placeholder="Reasoning for your decision..."
                  rows={3} />
      </div>

      {error && <div className="error-msg">{error}</div>}

      <button type="submit" disabled={loading} className="btn-primary full-width">
        {loading ? 'Submitting...' : '🚀 Submit Decision'}
      </button>
    </form>
  );
}