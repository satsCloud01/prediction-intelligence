import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Users, Plus, Sparkles, ArrowLeft, ChevronRight, Loader2, Edit3, Check, X, Trash2, UserPlus } from 'lucide-react'

const ROLES = ['economist','trader','analyst','journalist','policy_maker','activist','researcher','citizen','other']
const COLORS = ['#8b5cf6','#ef4444','#f59e0b','#10b981','#3b82f6','#ec4899','#06b6d4','#f97316']
const blank = () => ({ name:'', role:'economist', age:30, personality:'', background:'', beliefs:'', goals:'', avatar_color:'#8b5cf6' })

export default function EnvironmentSetup() {
  const { id: projectId } = useParams()
  const navigate = useNavigate()
  const [agents, setAgents] = useState([])
  const [project, setProject] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [agentCount, setAgentCount] = useState(5)
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState({})
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState(blank())
  const [confirmDeleteAll, setConfirmDeleteAll] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(null)

  const pid = projectId || null

  const load = async () => {
    if (!pid) return
    const [a, p] = await Promise.all([api.agents.list(pid), api.projects.get(pid)])
    setAgents(a)
    setProject(p)
  }
  useEffect(() => { load() }, [pid])

  const generate = async () => {
    setGenerating(true)
    try { await api.agents.generate(+pid, agentCount); load() }
    catch (err) { alert(err.message) }
    setGenerating(false)
  }

  const createAgent = async () => {
    await api.agents.create({ project_id: +pid, ...createForm, age: +createForm.age })
    setShowCreate(false)
    setCreateForm(blank())
    load()
  }

  const startEdit = (a) => {
    setEditingId(a.id)
    setEditForm({ name:a.name, role:a.role, age:a.age, personality:a.personality, background:a.background, beliefs:a.beliefs, goals:a.goals, avatar_color:a.avatar_color })
  }

  const saveEdit = async () => {
    await api.agents.update(editingId, { ...editForm, age: +editForm.age })
    setEditingId(null)
    load()
  }

  const deleteAgent = async (id) => {
    await api.agents.delete(id)
    setConfirmDelete(null)
    load()
  }

  const deleteAll = async () => {
    await api.agents.deleteAll(pid)
    setConfirmDeleteAll(false)
    load()
  }

  const initials = (name) => name.split(' ').map(n => n[0]).join('').slice(0,2).toUpperCase()

  const truncate = (s, len=80) => s && s.length > len ? s.slice(0, len) + '…' : s

  if (!pid) return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Environment Setup</h1>
      <p className="text-slate-400 mb-4">Select a project to generate agents.</p>
      <button onClick={() => navigate('/projects')} className="btn-primary">Go to Projects</button>
    </div>
  )

  const Field = ({ label, children }) => (
    <label className="block text-xs"><span className="text-slate-500 mb-1 block">{label}</span>{children}</label>
  )

  const FormFields = ({ form, setForm }) => (
    <div className="space-y-2">
      <Field label="Name"><input value={form.name} onChange={e => setForm({...form, name:e.target.value})} className="input w-full text-sm" /></Field>
      <div className="grid grid-cols-2 gap-2">
        <Field label="Role">
          <select value={form.role} onChange={e => setForm({...form, role:e.target.value})} className="select w-full text-xs">
            {ROLES.map(r => <option key={r} value={r}>{r.replace('_',' ')}</option>)}
          </select>
        </Field>
        <Field label="Age"><input type="number" value={form.age} onChange={e => setForm({...form, age:e.target.value})} className="input w-full text-xs" min={1} max={120} /></Field>
      </div>
      <Field label="Personality"><textarea value={form.personality} onChange={e => setForm({...form, personality:e.target.value})} className="textarea w-full text-xs" rows={2} /></Field>
      <Field label="Background"><textarea value={form.background} onChange={e => setForm({...form, background:e.target.value})} className="textarea w-full text-xs" rows={2} /></Field>
      <Field label="Beliefs"><textarea value={form.beliefs} onChange={e => setForm({...form, beliefs:e.target.value})} className="textarea w-full text-xs" rows={2} /></Field>
      <Field label="Goals"><textarea value={form.goals} onChange={e => setForm({...form, goals:e.target.value})} className="textarea w-full text-xs" rows={2} /></Field>
      <Field label="Color">
        <div className="flex gap-1.5 mt-1">{COLORS.map(c => (
          <button key={c} onClick={() => setForm({...form, avatar_color:c})}
            className={`w-6 h-6 rounded-full border-2 ${form.avatar_color === c ? 'border-white scale-110' : 'border-transparent'}`}
            style={{ backgroundColor: c }} />
        ))}</div>
      </Field>
    </div>
  )

  return (
    <div>
      <button onClick={() => navigate(`/projects/${pid}`)} className="btn-ghost flex items-center gap-1 mb-4 text-sm">
        <ArrowLeft className="w-4 h-4" /> Back to Project
      </button>

      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="w-6 h-6 text-violet-400" /> Step 2: Agent Personas
          </h1>
          <p className="text-sm text-slate-500">{project?.name}</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500">Count:</label>
            <input type="number" value={agentCount} onChange={e => setAgentCount(Math.min(20,Math.max(2,+e.target.value)))}
              className="input w-16 text-center" min={2} max={20} />
          </div>
          <button onClick={generate} disabled={generating} className="btn-primary flex items-center gap-2 disabled:opacity-50">
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {generating ? 'Generating…' : 'AI Generate'}
          </button>
          <button onClick={() => { setCreateForm(blank()); setShowCreate(true) }} className="btn-outline flex items-center gap-1.5">
            <UserPlus className="w-4 h-4" /> Add Agent
          </button>
          {agents.length > 0 && (
            confirmDeleteAll
              ? <div className="flex items-center gap-1">
                  <span className="text-xs text-red-400">Delete all?</span>
                  <button onClick={deleteAll} className="btn-ghost text-red-400 text-xs">Yes</button>
                  <button onClick={() => setConfirmDeleteAll(false)} className="btn-ghost text-xs">No</button>
                </div>
              : <button onClick={() => setConfirmDeleteAll(true)} className="btn-ghost text-red-400 flex items-center gap-1 text-xs">
                  <Trash2 className="w-3.5 h-3.5" /> Delete All
                </button>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setShowCreate(false)}>
          <div className="card w-full max-w-md max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2"><Plus className="w-5 h-5 text-violet-400" /> New Agent</h2>
            <FormFields form={createForm} setForm={setCreateForm} />
            <div className="flex gap-2 mt-4">
              <button onClick={createAgent} disabled={!createForm.name.trim()} className="btn-primary flex items-center gap-1 disabled:opacity-50">
                <Check className="w-4 h-4" /> Create
              </button>
              <button onClick={() => setShowCreate(false)} className="btn-ghost flex items-center gap-1"><X className="w-4 h-4" /> Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Agent Cards Grid */}
      {agents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map(a => (
            <div key={a.id} className="card hover:border-slate-700 transition-colors">
              {editingId === a.id ? (
                <div>
                  <FormFields form={editForm} setForm={setEditForm} />
                  <div className="flex gap-2 mt-3">
                    <button onClick={saveEdit} className="btn-primary text-xs flex items-center gap-1"><Check className="w-3 h-3" /> Save</button>
                    <button onClick={() => setEditingId(null)} className="btn-ghost text-xs flex items-center gap-1"><X className="w-3 h-3" /> Cancel</button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm shrink-0"
                        style={{ backgroundColor: a.avatar_color || '#8b5cf6' }}>
                        {initials(a.name || '?')}
                      </div>
                      <div>
                        <div className="font-medium text-sm">{a.name}</div>
                        <div className="text-xs text-slate-500">{a.role?.replace('_',' ')} · Age {a.age}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button onClick={() => startEdit(a)} className="text-slate-600 hover:text-violet-400 p-1"><Edit3 className="w-3.5 h-3.5" /></button>
                      {confirmDelete === a.id
                        ? <div className="flex items-center gap-0.5">
                            <button onClick={() => deleteAgent(a.id)} className="text-red-400 p-1 text-xs">Yes</button>
                            <button onClick={() => setConfirmDelete(null)} className="text-slate-500 p-1 text-xs">No</button>
                          </div>
                        : <button onClick={() => setConfirmDelete(a.id)} className="text-slate-600 hover:text-red-400 p-1"><Trash2 className="w-3.5 h-3.5" /></button>
                      }
                    </div>
                  </div>
                  <div className="space-y-1.5 text-xs">
                    {a.personality && <div><span className="text-slate-500">Personality:</span> <span className="text-slate-300">{truncate(a.personality)}</span></div>}
                    {a.background && <div><span className="text-slate-500">Background:</span> <span className="text-slate-300">{truncate(a.background)}</span></div>}
                    {a.beliefs && <div><span className="text-slate-500">Beliefs:</span> <span className="text-slate-300">{truncate(a.beliefs)}</span></div>}
                    {a.goals && <div><span className="text-slate-500">Goals:</span> <span className="text-slate-300">{truncate(a.goals)}</span></div>}
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center text-slate-600 py-16">
          <Users className="w-12 h-12 mx-auto mb-3 text-slate-700" />
          <p className="text-sm mb-4">No agent personas yet.</p>
          <div className="flex items-center justify-center gap-3">
            <button onClick={generate} disabled={generating} className="btn-primary flex items-center gap-2">
              <Sparkles className="w-4 h-4" /> Generate Agents
            </button>
            <button onClick={() => { setCreateForm(blank()); setShowCreate(true) }} className="btn-outline flex items-center gap-1.5">
              <UserPlus className="w-4 h-4" /> Add Agent
            </button>
          </div>
        </div>
      )}

      {agents.length > 0 && (
        <div className="flex items-center justify-between mt-6">
          <span className="badge">{agents.length} agent{agents.length !== 1 ? 's' : ''}</span>
          <button onClick={() => navigate(`/projects/${pid}/simulate`)} className="btn-primary flex items-center gap-2">
            Next: Run Simulation <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}
