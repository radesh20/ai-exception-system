import React from 'react';

const STATUS_CONFIG = {
  new:               { label: 'New',           color: '#6B7280', bg: '#F1F3F7' },
  analyzing:         { label: 'Analyzing',     color: '#1E40AF', bg: '#DBEAFE' },
  pending_decision:  { label: 'Needs Review',  color: '#92400E', bg: '#FEF3C7' },
  approved:          { label: 'Approved',      color: '#065F46', bg: '#CCFBF1' },
  rejected:          { label: 'Rejected',      color: '#6B7280', bg: '#F1F3F7' },
  executing:         { label: 'Executing',     color: '#1E40AF', bg: '#DBEAFE' },
  completed:         { label: 'Completed',     color: '#065F46', bg: '#CCFBF1' },
  failed:            { label: 'Failed',        color: '#991B1B', bg: '#FEE2E2' },
};

const PRIORITY_CONFIG = {
  1: { label: 'P1 Low',      color: '#065F46', bg: '#CCFBF1' },
  2: { label: 'P2',          color: '#6B7280', bg: '#F1F3F7' },
  3: { label: 'P3 Medium',   color: '#92400E', bg: '#FEF3C7' },
  4: { label: 'P4 High',     color: '#9A3412', bg: '#FFEDD5' },
  5: { label: 'P5 Critical', color: '#991B1B', bg: '#FEE2E2' },
};

export function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || { label: status, color: '#374151', bg: '#F1F3F7' };
  return (
    <span className="badge" style={{ color: cfg.color, background: cfg.bg }}>
      {cfg.label}
    </span>
  );
}

export function PriorityBadge({ priority }) {
  const cfg = PRIORITY_CONFIG[priority] || PRIORITY_CONFIG[3];
  return (
    <span className="badge" style={{ color: cfg.color, background: cfg.bg }}>
      {cfg.label}
    </span>
  );
}

export default StatusBadge;