import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { FolderKanban, Plus, Search, ChevronRight, Trash2 } from 'lucide-react'

const STATUS_COLORS = {
  draft: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  graph_built: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  env_ready: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  simulating: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  simulated: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  reported: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
}

const DOMAINS = ['general', 'finance', 'politics', 'geopolitics', 'technology', 'health', 'climate', 'social', 'creative']

export default function Projects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [search, setSearch] = useState('')
  const [form, setForm] = useState({ name: '', description: '', domain: 'general', prediction_goal: '', simulation_rounds: 10 })
  const navigate = useNavigate()

  const load = () => {
    api.projects.list().then(setProjects).catch(console.error).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const create = async () => {
    if (!form.name.trim()) return
    await api.projects.create(form)
    setShowCreate(false)
    setForm({ name: '', description: '', domain: 'general', prediction_goal: '', simulation_rounds: 10 })
    load()
  }

  const remove = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this project?')) return
    await api.projects.delete(id)
    load()
  }

  const filtered = projects.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.domain.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="text-sm text-slate-500">{projects.length} prediction projects</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search projects..."
          className="input w-full pl-10" />
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowCreate(false)}>
          <div className="card w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">New Prediction Project</h2>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-500 mb-1 block">Project Name</label>
                <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                  className="input w-full" placeholder="Q3 Market Outlook" />
              </div>
              <div>
                <label className="text-xs text-slate-500 mb-1 block">Description</label>
                <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
                  className="textarea w-full" rows={3} placeholder="Describe what you want to predict..." />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-500 mb-1 block">Domain</label>
                  <select value={form.domain} onChange={e => setForm({ ...form, domain: e.target.value })} className="select w-full">
                    {DOMAINS.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500 mb-1 block">Simulation Rounds</label>
                  <input type="number" value={form.simulation_rounds} onChange={e => setForm({ ...form, simulation_rounds: +e.target.value })}
                    className="input w-full" min={1} max={50} />
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-500 mb-1 block">Prediction Goal</label>
                <textarea value={form.prediction_goal} onChange={e => setForm({ ...form, prediction_goal: e.target.value })}
                  className="textarea w-full" rows={2} placeholder="What specific outcome are you trying to predict?" />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setShowCreate(false)} className="btn-ghost">Cancel</button>
              <button onClick={create} className="btn-primary">Create Project</button>
            </div>
          </div>
        </div>
      )}

      {/* Project List */}
      {loading ? (
        <div className="text-slate-500 py-20 text-center">Loading...</div>
      ) : (
        <div className="space-y-3">
          {filtered.map(p => (
            <div key={p.id} onClick={() => navigate(`/projects/${p.id}`)}
              className="card flex items-center justify-between cursor-pointer hover:border-slate-700 transition-colors">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center">
                  <FolderKanban className="w-5 h-5 text-brand-400" />
                </div>
                <div>
                  <div className="font-medium">{p.name}</div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    {p.domain} · Step {p.current_step}/5 · {p.agent_count} agents · {p.simulation_rounds} rounds
                  </div>
                  {p.prediction_goal && (
                    <div className="text-xs text-slate-600 mt-1 max-w-lg truncate">{p.prediction_goal}</div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`badge border ${STATUS_COLORS[p.status] || STATUS_COLORS.draft}`}>
                  {p.status.replace('_', ' ')}
                </span>
                <button onClick={e => remove(e, p.id)} className="text-slate-600 hover:text-red-400 transition-colors">
                  <Trash2 className="w-4 h-4" />
                </button>
                <ChevronRight className="w-4 h-4 text-slate-600" />
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="text-center text-slate-600 py-16 text-sm">
              {search ? 'No projects match your search' : 'No projects yet. Create your first prediction!'}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
