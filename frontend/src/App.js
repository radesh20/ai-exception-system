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
import Classifier from './pages/Classifier';
import AgentInteraction from './pages/AgentInteraction';
import HappyPathCases from './pages/HappyPathCases';
import HappyPathDetail from './pages/HappyPathDetail';
import ProcessInsights from './pages/ProcessInsights';
import ProcessAgents from './pages/ProcessAgents';
import api from './api';

function App() {
  const [config, setConfig] = useState(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    api.getConfig().then(c => { if (c) setConfig(c); }).catch(() => { });
    const refresh = () => {
      api.getPending().then(d => {
        if (Array.isArray(d)) setPendingCount(d.length);
      }).catch(() => { });
      api.getProcessInsightAlerts().then(d => {
        if (Array.isArray(d)) setAlertCount(d.length);
      }).catch(() => { });
    };
    refresh();
    const interval = setInterval(refresh, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app">
      <Navbar pendingCount={pendingCount} alertCount={alertCount} />
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard config={config} />} />
          <Route path="/incoming" element={<IncomingIssues />} />
          <Route path="/analysis" element={<AIAnalysis />} />
          <Route path="/decisions" element={<PendingDecisions onDecision={() => setPendingCount(c => Math.max(0, c - 1))} />} />
          <Route path="/actions" element={<ActionHistory />} />
          <Route path="/learning" element={<LearningInsights />} />
          <Route path="/classifier" element={<Classifier />} />
          <Route path="/settings" element={<Settings config={config} />} />
          <Route path="/exception/:id" element={<ExceptionDetail />} />
          <Route path="/agent-interactions" element={<AgentInteraction />} />
          <Route path="/happy-path" element={<HappyPathCases />} />
          <Route path="/happy-path/:id" element={<HappyPathDetail />} />
          <Route path="/process-insights" element={<ProcessInsights />} />
          <Route path="/process-agents" element={<ProcessAgents />} />
          <Route path="/process-agents/:caseId" element={<ProcessAgents />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;