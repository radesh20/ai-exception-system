import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Inbox, Brain, ClipboardCheck, Zap, TrendingUp, Settings } from 'lucide-react';

const NAV = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/incoming', icon: Inbox, label: 'Incoming Issues' },
  { path: '/analysis', icon: Brain, label: 'AI Analysis' },
  { path: '/decisions', icon: ClipboardCheck, label: 'Decisions', alert: true },
  { path: '/actions', icon: Zap, label: 'Actions' },
  { path: '/learning', icon: TrendingUp, label: 'Learning' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export default function Navbar({ pendingCount = 0 }) {
  const { pathname } = useLocation();
  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Brain size={18} /> P2P Exception AI
      </div>
      <div className="nav-links">
        {NAV.map(({ path, icon: Icon, label, alert }) => (
          <Link key={path} to={path}
            className={`nav-link${pathname === path ? ' active' : ''}`}>
            <Icon size={15} />
            {label}
            {alert && pendingCount > 0 && (
              <span className="nav-badge">{pendingCount}</span>
            )}
          </Link>
        ))}
      </div>
    </nav>
  );
}