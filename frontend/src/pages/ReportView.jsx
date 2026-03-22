import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { FileText, ArrowLeft, ChevronRight, Loader2, Sparkles, CheckCircle2, Target, Download, Edit3, Trash2, Check, X } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function ReportView() {
  const { id: projectId } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [reports, setReports] = useState([])
  const [selected, setSelected] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(false)
  const [draft, setDraft] = useState({ title: '', executive_summary: '', methodology: '' })
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(null)

  const pid = projectId || null

  const load = async () => {
    if (!pid) return
    const [r, p] = await Promise.all([api.reports.list(pid), api.projects.get(pid)])
    setReports(r)
    setProject(p)
    if (r.length > 0) {
      const detail = await api.reports.get(r[0].id)
      setSelected(detail)
      setDraft({ title: detail.title, executive_summary: detail.executive_summary, methodology: detail.methodology })
    }
  }
  useEffect(() => { load() }, [pid])

  const generate = async () => {
    setGenerating(true)
    try {
      await api.reports.generate(+pid)
      await load()
    } catch (err) { alert(err.message) }
    setGenerating(false)
  }

  const selectReport = async (r) => {
    const detail = await api.reports.get(r.id)
    setSelected(detail)
    setDraft({ title: detail.title, executive_summary: detail.executive_summary, methodology: detail.methodology })
    setEditing(false)
    setEditTitle(false)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await api.reports.update(selected.id, draft)
      setSelected({ ...selected, ...draft, ...updated })
      setEditing(false)
      setEditTitle(false)
    } catch (err) { alert(err.message) }
    setSaving(false)
  }

  const handleDelete = async (id) => {
    try {
      await api.reports.delete(id)
      setConfirmDelete(null)
      if (selected?.id === id) setSelected(null)
      await load()
    } catch (err) { alert(err.message) }
  }

  const handleExport = async () => {
    try {
      const data = await api.reports.export(selected.id)
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report-${selected.id}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) { alert(err.message) }
  }

  const confidenceData = selected?.predictions?.map((p, i) => ({
    name: `P${i + 1}`,
    confidence: Math.round((p.confidence || 0) * 100),
    prediction: p.prediction?.slice(0, 40) + '...',
  })) || []

  if (!pid) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-4">Reports</h1>
        <p className="text-slate-400 mb-4">Select a project to view reports.</p>
        <button onClick={() => navigate('/projects')} className="btn-primary">Go to Projects</button>
      </div>
    )
  }

  return (
    <div>
      <button onClick={() => navigate(`/projects/${pid}`)} className="btn-ghost flex items-center gap-1 mb-4 text-sm">
        <ArrowLeft className="w-4 h-4" /> Back to Project
      </button>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileText className="w-6 h-6 text-emerald-400" /> Step 4: Prediction Report
          </h1>
          <p className="text-sm text-slate-500">{project?.name}</p>
        </div>
        <div className="flex items-center gap-2">
          {selected && (
            <button onClick={handleExport} className="btn-outline flex items-center gap-2 text-sm">
              <Download className="w-4 h-4" /> Export
            </button>
          )}
          <button onClick={generate} disabled={generating} className="btn-primary flex items-center gap-2 disabled:opacity-50">
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {generating ? 'Generating...' : 'Generate Report'}
          </button>
        </div>
      </div>

      {reports.length > 1 && (
        <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
          {reports.map(r => (
            <div key={r.id} className="flex items-center gap-1">
              <button onClick={() => selectReport(r)}
                className={`badge border cursor-pointer whitespace-nowrap ${
                  selected?.id === r.id ? 'bg-brand-500/10 text-brand-400 border-brand-500/20' : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}>
                {r.title?.slice(0, 30)}...
              </button>
              {confirmDelete === r.id ? (
                <div className="flex items-center gap-1">
                  <button onClick={() => handleDelete(r.id)} className="text-red-400 hover:text-red-300"><Check className="w-3.5 h-3.5" /></button>
                  <button onClick={() => setConfirmDelete(null)} className="text-slate-400 hover:text-slate-300"><X className="w-3.5 h-3.5" /></button>
                </div>
              ) : (
                <button onClick={() => setConfirmDelete(r.id)} className="text-slate-600 hover:text-red-400">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {selected ? (
        <div className="space-y-4">
          {/* Header */}
          <div className="card border-brand-500/20">
            <div className="flex items-center justify-between mb-2">
              {editTitle ? (
                <div className="flex items-center gap-2 flex-1">
                  <input className="input text-lg font-bold flex-1" value={draft.title}
                    onChange={e => setDraft({ ...draft, title: e.target.value })} autoFocus />
                  <button onClick={() => { setEditTitle(false); handleSave() }} className="text-emerald-400"><Check className="w-4 h-4" /></button>
                  <button onClick={() => { setEditTitle(false); setDraft({ ...draft, title: selected.title }) }} className="text-slate-400"><X className="w-4 h-4" /></button>
                </div>
              ) : (
                <h2 className="text-lg font-bold cursor-pointer hover:text-brand-400 transition-colors"
                  onClick={() => setEditTitle(true)}>{selected.title}</h2>
              )}
              {reports.length === 1 && (
                confirmDelete === selected.id ? (
                  <div className="flex items-center gap-1">
                    <button onClick={() => handleDelete(selected.id)} className="text-red-400 hover:text-red-300 text-xs">Confirm</button>
                    <button onClick={() => setConfirmDelete(null)} className="text-slate-400 text-xs">Cancel</button>
                  </div>
                ) : (
                  <button onClick={() => setConfirmDelete(selected.id)} className="text-slate-600 hover:text-red-400">
                    <Trash2 className="w-4 h-4" />
                  </button>
                )
              )}
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-500 mb-4">
              <span>Confidence: <strong className="text-brand-400">{Math.round(selected.confidence_score * 100)}%</strong></span>
              <span>Generated: {new Date(selected.created_at).toLocaleDateString()}</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-3 mb-4">
              <div className="h-3 rounded-full bg-gradient-to-r from-brand-600 to-cyan-400 transition-all"
                style={{ width: `${selected.confidence_score * 100}%` }} />
            </div>
          </div>

          {/* Executive Summary */}
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold">Executive Summary</h3>
              <button onClick={() => setEditing(!editing)} className="btn-ghost text-xs flex items-center gap-1">
                <Edit3 className="w-3 h-3" /> {editing ? 'Cancel' : 'Edit'}
              </button>
            </div>
            {editing ? (
              <textarea className="textarea w-full min-h-[120px] text-sm" value={draft.executive_summary}
                onChange={e => setDraft({ ...draft, executive_summary: e.target.value })} />
            ) : (
              <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">{selected.executive_summary}</p>
            )}
          </div>

          {/* Key Findings */}
          <div className="card">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Key Findings
            </h3>
            <ul className="space-y-2">
              {selected.key_findings?.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
          </div>

          {/* Predictions Table */}
          <div className="card">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Target className="w-4 h-4 text-brand-400" /> Predictions
            </h3>
            <div className="space-y-3">
              {selected.predictions?.map((p, i) => (
                <div key={i} className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">{p.prediction}</span>
                    <span className="badge bg-brand-500/10 text-brand-400 border border-brand-500/20">
                      {Math.round((p.confidence || 0) * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-1.5">
                    <div className="h-1.5 rounded-full bg-brand-500 transition-all" style={{ width: `${(p.confidence || 0) * 100}%` }} />
                  </div>
                  {p.timeframe && <div className="text-xs text-slate-500 mt-1.5">Timeframe: {p.timeframe}</div>}
                </div>
              ))}
            </div>
          </div>

          {/* Confidence Chart */}
          {confidenceData.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold mb-3">Prediction Confidence Distribution</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={confidenceData}>
                  <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} domain={[0, 100]} />
                  <Tooltip content={({ active, payload }) => {
                    if (!active || !payload?.length) return null
                    const d = payload[0].payload
                    return (
                      <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs">
                        <div className="font-medium">{d.prediction}</div>
                        <div className="text-brand-400 mt-1">{d.confidence}% confidence</div>
                      </div>
                    )
                  }} />
                  <Bar dataKey="confidence" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Methodology */}
          <div className="card">
            <h3 className="text-sm font-semibold mb-3">Methodology</h3>
            {editing ? (
              <textarea className="textarea w-full min-h-[80px] text-sm" value={draft.methodology}
                onChange={e => setDraft({ ...draft, methodology: e.target.value })} />
            ) : (
              <p className="text-sm text-slate-400 leading-relaxed">{selected.methodology}</p>
            )}
          </div>

          {/* Save button in edit mode */}
          {editing && (
            <div className="flex justify-end">
              <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2 disabled:opacity-50">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center text-slate-600 py-16">
          <FileText className="w-12 h-12 mx-auto mb-3 text-slate-700" />
          <p className="text-sm">No reports yet. Complete a simulation first, then generate a prediction report.</p>
        </div>
      )}

      {selected && (
        <div className="flex justify-end mt-6">
          <button onClick={() => navigate(`/projects/${pid}/interact`)} className="btn-primary flex items-center gap-2">
            Next: Interact with Agents <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}
