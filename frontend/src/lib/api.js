import { getStoredKey, getStoredProvider, getStoredModel } from './llmContext'

const BASE = '/api'

function aiHeaders() {
  const key = getStoredKey()
  return key ? { 'X-Api-Key': key } : {}
}

function aiBody() {
  return {
    provider: getStoredProvider(),
    model: getStoredModel(),
  }
}

async function request(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...aiHeaders(), ...opts.headers },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `API error ${res.status}`)
  }
  return res.json()
}

async function get(path) { return request(path) }
async function post(path, body = {}) { return request(path, { method: 'POST', body: JSON.stringify(body) }) }
async function put(path, body = {}) { return request(path, { method: 'PUT', body: JSON.stringify(body) }) }
async function del(path) { return request(path, { method: 'DELETE' }) }

async function uploadFile(path, formData) {
  const res = await fetch(`${BASE}${path}`, { method: 'POST', body: formData, headers: aiHeaders() })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Upload error ${res.status}`)
  }
  return res.json()
}

export const api = {
  dashboard: {
    get: () => get('/dashboard'),
  },
  projects: {
    list: () => get('/projects'),
    get: (id) => get(`/projects/${id}`),
    create: (data) => post('/projects', data),
    update: (id, data) => put(`/projects/${id}`, data),
    delete: (id) => del(`/projects/${id}`),
  },
  graph: {
    seeds: (pid) => get(`/graph/${pid}/seeds`),
    getSeed: (id) => get(`/graph/seeds/${id}`),
    addSeed: (data) => post('/graph/seeds', data),
    updateSeed: (id, data) => put(`/graph/seeds/${id}`, data),
    deleteSeed: (id) => del(`/graph/seeds/${id}`),
    uploadSeed: (formData) => uploadFile('/graph/seeds/upload', formData),
    nodes: (pid) => get(`/graph/${pid}/nodes`),
    getNode: (id) => get(`/graph/nodes/${id}`),
    createNode: (data) => post('/graph/nodes', data),
    updateNode: (id, data) => put(`/graph/nodes/${id}`, data),
    deleteNode: (id) => del(`/graph/nodes/${id}`),
    edges: (pid) => get(`/graph/${pid}/edges`),
    createEdge: (data) => post('/graph/edges', data),
    updateEdge: (id, data) => put(`/graph/edges/${id}`, data),
    deleteEdge: (id) => del(`/graph/edges/${id}`),
    build: (pid) => post('/graph/build', { project_id: pid, ...aiBody() }),
  },
  agents: {
    list: (pid) => get(`/agents/${pid}`),
    get: (id) => get(`/agents/detail/${id}`),
    create: (data) => post('/agents', data),
    update: (id, data) => put(`/agents/detail/${id}`, data),
    delete: (id) => del(`/agents/detail/${id}`),
    generate: (pid, count = 5) => post('/agents/generate', { project_id: pid, count, ...aiBody() }),
    deleteAll: (pid) => del(`/agents/${pid}/all`),
  },
  simulation: {
    runs: (pid) => get(`/simulation/${pid}/runs`),
    getRun: (id) => get(`/simulation/runs/${id}`),
    events: (runId) => get(`/simulation/runs/${runId}/events`),
    messages: (runId) => get(`/simulation/runs/${runId}/messages`),
    createRun: (pid, rounds = 10) => post('/simulation/create', { project_id: pid, rounds, ...aiBody() }),
    runRound: (runId) => post('/simulation/round', { run_id: runId, ...aiBody() }),
    runAll: (pid, rounds = 10) => post('/simulation/run', { project_id: pid, rounds, ...aiBody() }),
    pause: (runId) => put(`/simulation/runs/${runId}/pause`),
    resume: (runId) => put(`/simulation/runs/${runId}/resume`),
    deleteRun: (runId) => del(`/simulation/runs/${runId}`),
  },
  reports: {
    list: (pid) => get(`/reports/${pid}`),
    get: (id) => get(`/reports/detail/${id}`),
    update: (id, data) => put(`/reports/detail/${id}`, data),
    delete: (id) => del(`/reports/detail/${id}`),
    export: (id) => get(`/reports/detail/${id}/export`),
    generate: (pid, runId) => post('/reports/generate', { project_id: pid, run_id: runId, ...aiBody() }),
  },
  interaction: {
    sessions: (pid) => get(`/interaction/${pid}/sessions`),
    startSession: (data) => post('/interaction/sessions', data),
    messages: (sid) => get(`/interaction/sessions/${sid}/messages`),
    chat: (sid, message) => post('/interaction/chat', { session_id: sid, message, ...aiBody() }),
  },
  settings: {
    providers: () => get('/settings/providers'),
    validateKey: (provider, key) => post('/settings/validate-key', { provider, key }),
    testKey: (provider, key, model) => post('/settings/test-key', { provider, key, model }),
  },
}
