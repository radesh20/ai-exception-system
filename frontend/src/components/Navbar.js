import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Inbox, Brain, ClipboardCheck, Settings, BarChart2, CheckCircle, TrendingUp, Cpu } from 'lucide-react';

const NAV = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/incoming', icon: Inbox, label: 'Incoming Issues' },
  { path: '/analysis', icon: Brain, label: 'AI Analysis' },
  { path: '/decisions', icon: ClipboardCheck, label: 'Decisions', alert: 'pending' },
  { path: '/classifier', icon: BarChart2, label: 'Classifier' },
  { path: '/settings', icon: Settings, label: 'Settings' },
  { path: '/happy-path', icon: CheckCircle, label: 'Happy Path Cases', greenDot: true },
  { path: '/process-insights', icon: TrendingUp, label: 'Process Insights', alert: 'insights' },
  { path: '/process-agents', icon: Cpu, label: 'Process Agents' },
];

export default function Navbar({ pendingCount = 0, alertCount = 0 }) {
  const { pathname } = useLocation()
  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Brain size={18} /> P2P Exception AI
      </div>
      <div className="nav-links">
        {NAV.map(({ path, icon: Icon, label, alert, greenDot }) => (
          <Link key={path} to={path}
            className={`nav-link${pathname === path || (path !== '/' && path.length > 1 && pathname.startsWith(path) && (pathname.length === path.length || pathname[path.length] === '/')) ? ' active' : ''}`}>
            <Icon size={15} />
            {label}
            {greenDot && (
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#16A34A', display: 'inline-block', marginLeft: 4 }} />
            )}
            {alert === 'pending' && pendingCount > 0 && (
              <span className="nav-badge">{pendingCount}</span>
            )}
            {alert === 'insights' && alertCount > 0 && (
              <span className="nav-badge" style={{ background: '#DC2626' }}>{alertCount}</span>
            )}
          </Link>
        ))}
      </div>
    </nav>
  );
}