import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const NAV = [
  { path: '/',          icon: '📊', label: 'Dashboard' },
  { path: '/incoming',  icon: '📥', label: 'Incoming Issues' },
  { path: '/analysis',  icon: '🤖', label: 'AI Analysis' },
  { path: '/decisions', icon: '👤', label: 'Decisions',  alert: true },
  { path: '/actions',   icon: '⚡', label: 'Actions' },
  { path: '/learning',  icon: '📈', label: 'Learning' },
  { path: '/settings',  icon: '⚙️', label: 'Settings' },
];

export default function Navbar({ pendingCount = 0 }) {
  const { pathname } = useLocation();
  return (
    <nav className="navbar">
      <div className="nav-brand">🤖 P2P Exception AI</div>
      <div className="nav-links">
        {NAV.map(({ path, icon, label, alert }) => (
          <Link key={path} to={path}
            className={`nav-link${pathname === path ? ' active' : ''}`}>
            {icon} {label}
            {alert && pendingCount > 0 && (
              <span className="nav-badge">{pendingCount}</span>
            )}
          </Link>
        ))}
      </div>
    </nav>
  );
}