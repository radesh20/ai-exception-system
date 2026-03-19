import React from 'react';
import { Link } from 'react-router-dom';
import { DollarSign, FolderOpen, Building2 } from 'lucide-react';
import { StatusBadge, PriorityBadge } from './StatusBadge';

export default function ExceptionCard({ exc, compact = false }) {
  const ctx = exc.context || {};
  const cls = exc.classification || {};
  const rc = exc.root_cause || {};

  return (
    <div className={`exception-card priority-border-${cls.priority || 1}`}>
      <div className="card-top">
        <div className="card-badges">
          <StatusBadge status={exc.status} />
          <PriorityBadge priority={cls.priority} />
          {cls.is_novel && <span className="badge badge-novel">Novel</span>}
        </div>
        <span className="card-id">#{exc.id?.slice(0, 12)}</span>
      </div>

      <div className="card-type">{ctx.exception_type?.replace(/_/g, ' ')}</div>

      <div className="card-meta">
        <span><DollarSign /> ${(ctx.financial_exposure || 0).toLocaleString()}</span>
        <span><FolderOpen /> {cls.category?.replace(/_/g, ' ')}</span>
        <span><Building2 /> {ctx.vendor}</span>
      </div>

      {!compact && rc.hypothesis && (
        <div className="card-hypothesis">
          {rc.hypothesis.slice(0, 120)}...
        </div>
      )}

      {!compact && exc.recommended_action && (
        <div className="card-action">
          <strong>Recommended:</strong> {exc.recommended_action.replace(/_/g, ' ')}
        </div>
      )}

      <div className="card-footer">
        <span className="card-time">
          {new Date(exc.created_at).toLocaleDateString()}
        </span>
        <Link to={`/exception/${exc.id}`} className="card-link">
          View Details →
        </Link>
      </div>
    </div>
  );
}