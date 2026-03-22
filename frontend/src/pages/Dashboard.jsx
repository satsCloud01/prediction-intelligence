import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import {
  FolderKanban, Users, Play, FileText, Zap, Plus, ChevronRight,
  TrendingUp, BarChart3, Activity,
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const STATUS_COLORS = {
  draft: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  graph_built: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  env_ready: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  simulating: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  simulated: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  reported: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
}

const PIE_COLORS = ['#06b6d4', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444', '#ec4899']

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.dashboard.get().then(setData).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-slate-500 py-20 text-center">Loading dashboard...</div>
  if (!data) return <div className="text-red-400 py-20 text-center">Failed to load dashboard</div>

  const { stats, status_distribution, domain_distribution, recent_projects } = data

  const statusData = Object.entries(status_distribution).map(([k, v]) => ({ name: k.replace('_', ' '), value: v }))
  const domainData = Object.entries(domain_distribution).map(([k, v]) => ({ name: k, value: v }))

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-slate-500">Swarm intelligence prediction overview</p>
        </div>
        <button onClick={() => navigate('/projects')} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        {[
          { icon: FolderKanban, label: 'Projects', value: stats.total_projects, color: 'text-brand-400' },
          { icon: Users, label: 'Agents', value: stats.total_agents, color: 'text-violet-400' },
          { icon: Play, label: 'Simulations', value: stats.total_simulations, color: 'text-orange-400' },
          { icon: FileText, label: 'Reports', value: stats.total_reports, color: 'text-emerald-400' },
          { icon: Zap, label: 'Tokens Used', value: stats.total_tokens_used.toLocaleString(), color: 'text-pink-400' },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="flex items-center gap-2 text-slate-500 text-xs">
              <s.icon className={`w-3.5 h-3.5 ${s.color}`} />
              {s.label}
            </div>
            <div className="text-xl font-bold">{s.value}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
        <div className="card">
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-brand-400" /> Project Status
          </h3>
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={statusData}>
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: 8 }} />
                <Bar dataKey="value" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-slate-600 text-sm text-center py-10">No data yet</div>
          )}
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-violet-400" /> Domain Distribution
          </h3>
          {domainData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={domainData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name }) => name}>
                  {domainData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-slate-600 text-sm text-center py-10">No data yet</div>
          )}
        </div>
      </div>

      {/* Recent Projects */}
      <div className="card">
        <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-brand-400" /> Recent Projects
        </h3>
        <div className="space-y-2">
          {recent_projects.map(p => (
            <div
              key={p.id}
              onClick={() => navigate(`/projects/${p.id}`)}
              className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-800/60 cursor-pointer transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-brand-500/10 flex items-center justify-center">
                  <FolderKanban className="w-4 h-4 text-brand-400" />
                </div>
                <div>
                  <div className="text-sm font-medium">{p.name}</div>
                  <div className="text-xs text-slate-500">{p.domain} · Step {p.current_step}/5 · {p.agent_count} agents</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`badge border ${STATUS_COLORS[p.status] || STATUS_COLORS.draft}`}>
                  {p.status.replace('_', ' ')}
                </span>
                <ChevronRight className="w-4 h-4 text-slate-600" />
              </div>
            </div>
          ))}
          {recent_projects.length === 0 && (
            <div className="text-center text-slate-600 py-8 text-sm">
              No projects yet. Create your first prediction project!
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
