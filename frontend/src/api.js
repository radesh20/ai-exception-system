const BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const req = async (path, options = {}) => {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    console.error(`API Error: ${res.status} ${path}`);
    return res.status === 404 ? null : [];
  }
  return res.json();
};

const api = {
  // Config
  getConfig:    () => req('/api/config'),
  health:       () => req('/api/health'),

  // Exceptions
  getExceptions: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return req(`/api/exceptions${q ? '?' + q : ''}`);
  },
  getPending:    () => req('/api/exceptions/pending'),
  getException:  (id) => req(`/api/exceptions/${id}`),
  processCase:   (raw_input) => req('/api/process', {
    method: 'POST', body: JSON.stringify({ raw_input })
  }),
  processAll:    () => req('/api/process-all', { method: 'POST' }),

  // Variants
  getVariants:   () => req('/api/variants'),
  getVariantStats: () => req('/api/stats/variants'),

  // Decisions
  submitDecision: (data) => req('/api/decisions', {
    method: 'POST', body: JSON.stringify(data)
  }),
  getDecisions:  () => req('/api/decisions'),

  // Actions
  getActions:    () => req('/api/actions'),
  getExceptionActions: (id) => req(`/api/actions/${id}`),

  // Stats
  getStats:      () => req('/api/stats'),

  // Learning
  getLearning:         () => req('/api/learning'),
  getPolicyPerf:       () => req('/api/learning/policies'),
  getLearningHistory:  () => req('/api/learning/history'),

  // Agent Trace
  getTrace:      (id) => req(`/api/exceptions/${id}/trace`),

  // Categories & Batch
  getCategories:       () => req('/api/categories'),
  getCategoryPending:  (cat, limit = 5) => req(`/api/categories/${cat}/pending?limit=${limit}`),
  processNextBatch:    (cat, size = 5) => req(`/api/categories/${cat}/process-next-batch?batch_size=${size}`, { method: 'POST' }),
};

export default api;