import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Users, Search, ChevronRight } from 'lucide-react'

export default function AgentGallery() {
  const [projects, setProjects] = useState([])
  const [allAgents, setAllAgents] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const load = async () => {
      try {
        const projs = await api.projects.list()
        setProjects(projs)
        const agentArrays = await Promise.all(
          projs.filter(p => p.agent_count > 0).map(async p => {
            const agents = await api.agents.list(p.id)
            return agents.map(a => ({ ...a, projectId: p.id, projectName: p.name }))
          })
        )
        setAllAgents(agentArrays.flat())
      } catch (err) { console.error(err) }
      setLoading(false)
    }
    load()
  }, [])

  const filtered = allAgents.filter(a =>
    a.name.toLowerCase().includes(search.toLowerCase()) ||
    a.role.toLowerCase().includes(search.toLowerCase()) ||
    a.projectName.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="w-6 h-6 text-violet-400" /> Agent Gallery
          </h1>
          <p className="text-sm text-slate-500">{allAgents.length} agents across {projects.filter(p => p.agent_count > 0).length} projects</p>
        </div>
      </div>

      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search agents by name, role, or project..."
          className="input w-full pl-10" />
      </div>

      {loading ? (
        <div className="text-slate-500 py-20 text-center">Loading agents...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(a => (
            <div key={`${a.projectId}-${a.id}`}
              className="card hover:border-slate-700 transition-colors cursor-pointer"
              onClick={() => navigate(`/projects/${a.projectId}/agents`)}>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm"
                  style={{ backgroundColor: a.avatar_color }}>
                  {a.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                </div>
                <div>
                  <div className="font-medium text-sm">{a.name}</div>
                  <div className="text-xs text-slate-500">{a.role} · Age {a.age}</div>
                </div>
              </div>
              <div className="text-xs text-slate-400 mb-2 line-clamp-2">{a.personality}</div>
              <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-800">
                <span className="badge bg-brand-500/10 text-brand-400 border border-brand-500/20 text-xs">{a.projectName}</span>
                <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center text-slate-600 py-16 text-sm">
          {search ? 'No agents match your search' : 'No agents generated yet. Create a project and run Step 2.'}
        </div>
      )}
    </div>
  )
}
