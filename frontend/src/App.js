import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import IncomingIssues from './pages/IncomingIssues';
import AIAnalysis from './pages/AIAnalysis';
import PendingDecisions from './pages/PendingDecisions';
import ActionHistory from './pages/ActionHistory';
import LearningInsights from './pages/LearningInsights';
import ExceptionDetail from './pages/ExceptionDetail';
import Settings from './pages/Settings';
import api from './api';

function App() {
  const [config, setConfig] = useState(null);
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    api.getConfig().then(c => { if (c) setConfig(c); }).catch(() => {});
    const refresh = () => {
      api.getPending().then(d => {
        if (Array.isArray(d)) setPendingCount(d.length);
      }).catch(() => {});
    };
    refresh();
    const interval = setInterval(refresh, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app">
      <Navbar pendingCount={pendingCount} />
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard config={config} />} />
          <Route path="/incoming" element={<IncomingIssues />} />
          <Route path="/analysis" element={<AIAnalysis />} />
          <Route path="/decisions" element={<PendingDecisions onDecision={() => setPendingCount(c => Math.max(0, c - 1))} />} />
          <Route path="/actions" element={<ActionHistory />} />
          <Route path="/learning" element={<LearningInsights />} />
          <Route path="/settings" element={<Settings config={config} />} />
          <Route path="/exception/:id" element={<ExceptionDetail />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;