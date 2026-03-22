import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Play, Pause, SkipForward, Plus, Trash2, ArrowLeft, ArrowRight, Loader2, CheckCircle2, Clock, AlertCircle } from 'lucide-react'
import { api } from '../lib/api'

const TYPE_COLORS = {
  interaction: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  opinion_shift: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
  conflict: 'bg-red-500/20 text-red-400 border-red-500/30',
  consensus: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  event: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
}

const STATUS_ICON = {
  pending: <Clock className="w-4 h-4 text-zinc-400" />,
  running: <Loader2 className="w-4 h-4 text-orange-400 animate-spin" />,
  paused: <Pause className="w-4 h-4 text-yellow-400" />,
  completed: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
}

export default function SimulationRunner() {
  const { id: pid } = useParams()
  const navigate = useNavigate()
  const [rounds, setRounds] = useState(10)
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [events, setEvents] = useState([])
  const [roundLoading, setRoundLoading] = useState(false)
  const [allLoading, setAllLoading] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)
  const eventsRef = useRef(null)

  useEffect(() => { fetchRuns() }, [pid])

  async function fetchRuns() {
    try {
      const data = await api.simulation.runs(pid)
      setRuns(data)
      if (data.length && !selectedRun) selectRun(data[0])
    } catch { /* empty */ }
  }

  async function selectRun(run) {
    setSelectedRun(run)
    try {
      const ev = await api.simulation.events(run.id)
      setEvents(ev)
    } catch { setEvents([]) }
  }

  async function refreshSelected(runId) {
    try {
      const run = await api.simulation.getRun(runId)
      setSelectedRun(run)
      setRuns(prev => prev.map(r => r.id === runId ? run : r))
      const ev = await api.simulation.events(runId)
      setEvents(ev)
    } catch { /* empty */ }
  }

  async function handleRunAll() {
    setAllLoading(true)
    try {
      const run = await api.simulation.runAll(+pid, rounds)
      await fetchRuns()
      if (run?.id) await refreshSelected(run.id)
    } catch (e) { alert(e.message) }
    setAllLoading(false)
  }

  async function handleCreate() {
    setCreateLoading(true)
    try {
      const run = await api.simulation.createRun(+pid, rounds)
      setRuns(prev => [run, ...prev])
      setSelectedRun(run)
      setEvents([])
    } catch (e) { alert(e.message) }
    setCreateLoading(false)
  }

  async function handleNextRound() {
    if (!selectedRun) return
    setRoundLoading(true)
    try {
      await api.simulation.runRound(selectedRun.id)
      await refreshSelected(selectedRun.id)
      setTimeout(() => eventsRef.current?.scrollTo({ top: eventsRef.current.scrollHeight, behavior: 'smooth' }), 100)
    } catch (e) { alert(e.message) }
    setRoundLoading(false)
  }

  async function handlePause() {
    if (!selectedRun) return
    try { await api.simulation.pause(selectedRun.id); await refreshSelected(selectedRun.id) } catch (e) { alert(e.message) }
  }

  async function handleResume() {
    if (!selectedRun) return
    try { await api.simulation.resume(selectedRun.id); await refreshSelected(selectedRun.id) } catch (e) { alert(e.message) }
  }

  async function handleDelete(runId, e) {
    e.stopPropagation()
    if (!confirm('Delete this run?')) return
    try {
      await api.simulation.deleteRun(runId)
      setRuns(prev => prev.filter(r => r.id !== runId))
      if (selectedRun?.id === runId) { setSelectedRun(null); setEvents([]) }
    } catch (err) { alert(err.message) }
  }

  // Sentiment chart data: average sentiment per round
  const chartData = (() => {
    const byRound = {}
    events.forEach(ev => {
      const r = ev.round_num ?? ev.round ?? 0
      if (!byRound[r]) byRound[r] = { round: r, values: [] }
      if (ev.sentiment != null) byRound[r].values.push(ev.sentiment)
    })
    return Object.values(byRound)
      .sort((a, b) => a.round - b.round)
      .map(d => ({ round: d.round, sentiment: d.values.length ? +(d.values.reduce((s, v) => s + v, 0) / d.values.length).toFixed(2) : 0 }))
  })()

  // Group events by round
  const grouped = {}
  events.forEach(ev => {
    const r = ev.round_num ?? ev.round ?? 0
    if (!grouped[r]) grouped[r] = []
    grouped[r].push(ev)
  })

  const totalRounds = selectedRun?.total_rounds ?? selectedRun?.rounds ?? 1
  const currentRound = selectedRun?.current_round ?? 0
  const progress = (currentRound / totalRounds) * 100
  const canStep = selectedRun && ['pending', 'running', 'paused'].includes(selectedRun.status) && currentRound < totalRounds

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(`/projects/${pid}`)} className="btn-ghost p-2"><ArrowLeft className="w-5 h-5" /></button>
          <h1 className="text-2xl font-bold">Simulation Runner</h1>
          <AlertCircle className="w-5 h-5 text-orange-400" />
        </div>
        <button onClick={() => navigate(`/projects/${pid}/report`)} className="btn-outline flex items-center gap-2">
          Report <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Left column: Controls + Run History */}
        <div className="col-span-4 space-y-4">
          {/* Controls card */}
          <div className="card p-4 space-y-3">
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide">Controls</h2>
            <div className="flex items-center gap-2">
              <label className="text-sm text-zinc-400">Rounds</label>
              <input type="number" min={1} max={50} value={rounds}
                onChange={e => setRounds(Math.max(1, Math.min(50, +e.target.value)))}
                className="input w-20 text-center" />
            </div>
            <div className="flex gap-2">
              <button onClick={handleRunAll} disabled={allLoading}
                className="btn-primary flex-1 flex items-center justify-center gap-2 text-sm">
                {allLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Run All Rounds
              </button>
              <button onClick={handleCreate} disabled={createLoading}
                className="btn-outline flex-1 flex items-center justify-center gap-2 text-sm">
                {createLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                Create Run
              </button>
            </div>
            {selectedRun && (
              <div className="flex gap-2">
                <button onClick={handleNextRound} disabled={roundLoading || !canStep}
                  className="btn-primary flex-1 flex items-center justify-center gap-2 text-sm disabled:opacity-40">
                  {roundLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <SkipForward className="w-4 h-4" />}
                  Next Round
                </button>
                {selectedRun.status === 'running' && (
                  <button onClick={handlePause} className="btn-outline px-3"><Pause className="w-4 h-4" /></button>
                )}
                {selectedRun.status === 'paused' && (
                  <button onClick={handleResume} className="btn-outline px-3"><Play className="w-4 h-4" /></button>
                )}
              </div>
            )}
          </div>

          {/* Progress card */}
          {selectedRun && (
            <div className="card p-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-zinc-400">Progress</span>
                <div className="flex items-center gap-2">
                  {STATUS_ICON[selectedRun.status]}
                  <span className="badge">{selectedRun.status}</span>
                  <span className="text-zinc-500">{currentRound}/{totalRounds}</span>
                </div>
              </div>
              <div className="w-full bg-zinc-800 rounded-full h-2">
                <div className="bg-orange-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, progress)}%` }} />
              </div>
            </div>
          )}

          {/* Run History */}
          <div className="card p-4 space-y-2">
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide">Run History</h2>
            {runs.length === 0 && <p className="text-sm text-zinc-500">No runs yet.</p>}
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {runs.map(run => (
                <div key={run.id} onClick={() => selectRun(run)}
                  className={`flex items-center justify-between p-2 rounded cursor-pointer text-sm hover:bg-zinc-800 ${
                    selectedRun?.id === run.id ? 'bg-zinc-800 border border-orange-500/30' : ''
                  }`}>
                  <div className="flex items-center gap-2 min-w-0">
                    {STATUS_ICON[run.status]}
                    <span className="truncate">Run #{String(run.id).slice(-6)}</span>
                    <span className="text-zinc-500">{run.current_round ?? 0}/{run.total_rounds ?? run.rounds ?? 0}r</span>
                  </div>
                  <button onClick={e => handleDelete(run.id, e)}
                    className="btn-ghost p-1 opacity-50 hover:opacity-100">
                    <Trash2 className="w-3.5 h-3.5 text-red-400" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Consensus Summary */}
          {selectedRun?.status === 'completed' && selectedRun.summary && (
            <div className="card p-4 space-y-2 border-emerald-500/20">
              <h2 className="text-sm font-semibold text-emerald-400 uppercase tracking-wide">Consensus Summary</h2>
              <p className="text-sm text-zinc-300 leading-relaxed">{selectedRun.summary}</p>
            </div>
          )}
        </div>

        {/* Right column: Chart + Events */}
        <div className="col-span-8 space-y-4">
          {/* Sentiment Chart */}
          <div className="card p-4">
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide mb-3">Sentiment Timeline</h2>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <XAxis dataKey="round" tick={{ fill: '#71717a', fontSize: 12 }} axisLine={{ stroke: '#3f3f46' }} tickLine={false} />
                  <YAxis domain={[-1, 1]} tick={{ fill: '#71717a', fontSize: 12 }} axisLine={{ stroke: '#3f3f46' }} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', borderRadius: 8, color: '#e4e4e7' }} />
                  <Line type="monotone" dataKey="sentiment" stroke="#f97316" strokeWidth={2}
                    dot={{ fill: '#f97316', r: 3 }} activeDot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[200px] flex items-center justify-center text-zinc-600 text-sm">
                Run a simulation to see sentiment data
              </div>
            )}
          </div>

          {/* Events Timeline */}
          <div className="card p-4">
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide mb-3">
              Events Timeline <span className="text-zinc-600 ml-1">({events.length})</span>
            </h2>
            <div ref={eventsRef} className="space-y-4 max-h-[480px] overflow-y-auto pr-2">
              {Object.keys(grouped).length === 0 && (
                <p className="text-sm text-zinc-600 text-center py-8">
                  No events yet. Create and run a simulation above.
                </p>
              )}
              {Object.entries(grouped).sort(([a], [b]) => +a - +b).map(([round, evts]) => (
                <div key={round}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded">
                      Round {round}
                    </span>
                    <div className="flex-1 border-t border-zinc-800" />
                  </div>
                  <div className="space-y-1.5 ml-2">
                    {evts.map((ev, i) => (
                      <div key={ev.id || i}
                        className="flex items-start gap-3 p-2 rounded bg-zinc-900/50 hover:bg-zinc-900 text-sm">
                        <span className={`badge border text-xs whitespace-nowrap ${
                          TYPE_COLORS[ev.event_type] || TYPE_COLORS.event
                        }`}>
                          {ev.event_type || 'event'}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-zinc-300">{ev.description || ev.content || '\u2014'}</p>
                          <div className="flex items-center gap-3 mt-1 text-xs text-zinc-500">
                            {ev.agents_involved?.length > 0 && (
                              <span>Agents: {ev.agents_involved.join(', ')}</span>
                            )}
                            {ev.agent_name && <span>Agent: {ev.agent_name}</span>}
                            {ev.sentiment != null && (
                              <span>Sentiment: <span className={ev.sentiment >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                                {ev.sentiment.toFixed(2)}
                              </span></span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
