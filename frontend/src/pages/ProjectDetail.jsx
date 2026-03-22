import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import {
  Network, Users, Play, FileText, MessageCircle, ChevronRight,
  CheckCircle2, Circle, ArrowLeft,
} from 'lucide-react'

const STEPS = [
  { num: 1, icon: Network, label: 'Graph Build', desc: 'Upload seeds & build knowledge graph', route: 'graph', statuses: ['draft'] },
  { num: 2, icon: Users, label: 'Environment Setup', desc: 'Generate agent personas', route: 'agents', statuses: ['graph_built'] },
  { num: 3, icon: Play, label: 'Simulation', desc: 'Run swarm intelligence simulation', route: 'simulate', statuses: ['env_ready'] },
  { num: 4, icon: FileText, label: 'Report', desc: 'Generate prediction report', route: 'report', statuses: ['simulated'] },
  { num: 5, icon: MessageCircle, label: 'Interaction', desc: 'Chat with simulated agents', route: 'interact', statuses: ['reported'] },
]

export default function ProjectDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.projects.get(id).then(setProject).catch(console.error).finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="text-slate-500 py-20 text-center">Loading...</div>
  if (!project) return <div className="text-red-400 py-20 text-center">Project not found</div>

  return (
    <div>
      <button onClick={() => navigate('/projects')} className="btn-ghost flex items-center gap-1 mb-4 text-sm">
        <ArrowLeft className="w-4 h-4" /> Back to Projects
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold">{project.name}</h1>
        <p className="text-sm text-slate-500 mt-1">{project.description}</p>
        {project.prediction_goal && (
          <p className="text-sm text-slate-400 mt-2">
            <span className="text-brand-400 font-medium">Goal:</span> {project.prediction_goal}
          </p>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-8">
        {[
          { label: 'Seeds', value: project.counts.seeds },
          { label: 'Graph Nodes', value: project.counts.nodes },
          { label: 'Agents', value: project.counts.agents },
          { label: 'Simulations', value: project.counts.simulations },
          { label: 'Reports', value: project.counts.reports },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="text-xs text-slate-500">{s.label}</div>
            <div className="text-lg font-bold">{s.value}</div>
          </div>
        ))}
      </div>

      {/* Pipeline Steps */}
      <div className="card mb-6">
        <h3 className="text-sm font-semibold mb-4">Prediction Pipeline</h3>
        <div className="space-y-3">
          {STEPS.map((step) => {
            const isCompleted = project.current_step > step.num
            const isCurrent = project.current_step === step.num
            const isLocked = project.current_step < step.num

            return (
              <div
                key={step.num}
                onClick={() => !isLocked && navigate(`/projects/${id}/${step.route}`)}
                className={`flex items-center justify-between p-4 rounded-lg border transition-colors ${
                  isCurrent
                    ? 'border-brand-500/30 bg-brand-500/5 cursor-pointer hover:bg-brand-500/10'
                    : isCompleted
                    ? 'border-emerald-500/20 bg-emerald-500/5 cursor-pointer hover:bg-emerald-500/10'
                    : 'border-slate-800 bg-slate-900/50 opacity-50'
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    isCompleted ? 'bg-emerald-500/20' : isCurrent ? 'bg-brand-500/20' : 'bg-slate-800'
                  }`}>
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <Circle className={`w-4 h-4 ${isCurrent ? 'text-brand-400' : 'text-slate-600'}`} />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <step.icon className={`w-4 h-4 ${isCompleted ? 'text-emerald-400' : isCurrent ? 'text-brand-400' : 'text-slate-600'}`} />
                      <span className="text-sm font-medium">Step {step.num}: {step.label}</span>
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">{step.desc}</div>
                  </div>
                </div>
                {!isLocked && <ChevronRight className="w-4 h-4 text-slate-500" />}
              </div>
            )
          })}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3">
        {project.current_step <= 5 && (
          <button
            onClick={() => {
              const step = STEPS.find(s => s.num === project.current_step)
              if (step) navigate(`/projects/${id}/${step.route}`)
            }}
            className="btn-primary flex items-center gap-2"
          >
            Continue to Step {project.current_step} <ChevronRight className="w-4 h-4" />
          </button>
        )}
        {project.counts.reports > 0 && (
          <button onClick={() => navigate(`/projects/${id}/report`)} className="btn-outline flex items-center gap-2">
            <FileText className="w-4 h-4" /> View Report
          </button>
        )}
      </div>
    </div>
  )
}
