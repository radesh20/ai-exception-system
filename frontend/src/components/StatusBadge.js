import React from 'react';

const STATUS_CONFIG = {
  new:               { label: 'New',           color: '#6c757d', bg: '#f8f9fa' },
  analyzing:         { label: 'Analyzing',     color: '#0d6efd', bg: '#e7f3ff' },
  pending_decision:  { label: 'Needs Review',  color: '#dc3545', bg: '#fde8e8' },
  approved:          { label: 'Approved',      color: '#198754', bg: '#d4edda' },
  rejected:          { label: 'Rejected',      color: '#6c757d', bg: '#e9ecef' },
  executing:         { label: 'Executing',     color: '#0d6efd', bg: '#e7f3ff' },
  completed:         { label: 'Completed',     color: '#198754', bg: '#d4edda' },
  failed:            { label: 'Failed',        color: '#dc3545', bg: '#f8d7da' },
};

const PRIORITY_CONFIG = {
  1: { label: 'P1 Low',      color: '#198754', bg: '#d4edda' },
  2: { label: 'P2',          color: '#6c757d', bg: '#e9ecef' },
  3: { label: 'P3 Medium',   color: '#ffc107', bg: '#fff3cd' },
  4: { label: 'P4 High',     color: '#fd7e14', bg: '#ffe5d0' },
  5: { label: 'P5 Critical', color: '#dc3545', bg: '#f8d7da' },
};

export function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || { label: status, color: '#333', bg: '#eee' };
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