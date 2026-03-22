import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { MessageCircle, ArrowLeft, Send, Loader2, Users, Brain, Plus } from 'lucide-react'

export default function Interaction() {
  const { id: projectId } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [agents, setAgents] = useState([])
  const [sessions, setSessions] = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const chatEnd = useRef(null)

  const pid = projectId || null

  const load = async () => {
    if (!pid) return
    const [a, s, p] = await Promise.all([
      api.agents.list(pid), api.interaction.sessions(pid), api.projects.get(pid),
    ])
    setAgents(a)
    setSessions(s)
    setProject(p)
  }
  useEffect(() => { load() }, [pid])

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const startSession = async (agentId, type = 'agent') => {
    const res = await api.interaction.startSession({
      project_id: +pid,
      agent_persona_id: agentId,
      session_type: type,
    })
    setActiveSession(res)
    setMessages([])
    load()
  }

  const selectSession = async (s) => {
    setActiveSession(s)
    const msgs = await api.interaction.messages(s.id)
    setMessages(msgs)
  }

  const send = async () => {
    if (!input.trim() || !activeSession) return
    const msg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: msg, id: Date.now() }])
    setSending(true)
    try {
      const res = await api.interaction.chat(activeSession.session_id || activeSession.id, msg)
      setMessages(prev => [...prev, { role: 'assistant', content: res.response, id: Date.now() + 1 }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}`, id: Date.now() + 1 }])
    }
    setSending(false)
  }

  if (!pid) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-4">Interaction</h1>
        <p className="text-slate-400 mb-4">Select a project to chat with agents.</p>
        <button onClick={() => navigate('/projects')} className="btn-primary">Go to Projects</button>
      </div>
    )
  }

  return (
    <div>
      <button onClick={() => navigate(`/projects/${pid}`)} className="btn-ghost flex items-center gap-1 mb-4 text-sm">
        <ArrowLeft className="w-4 h-4" /> Back to Project
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <MessageCircle className="w-6 h-6 text-pink-400" /> Step 5: Deep Interaction
        </h1>
        <p className="text-sm text-slate-500">{project?.name}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4" style={{ height: 600 }}>
        {/* Agent Panel */}
        <div className="card overflow-y-auto">
          <h3 className="text-sm font-semibold mb-3">Agents</h3>

          {/* Analyst option */}
          <button onClick={() => startSession(null, 'analyst')}
            className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-slate-800 transition-colors mb-2 text-left">
            <div className="w-8 h-8 rounded-full bg-brand-500/20 flex items-center justify-center">
              <Brain className="w-4 h-4 text-brand-400" />
            </div>
            <div>
              <div className="text-xs font-medium">Analysis Agent</div>
              <div className="text-xs text-slate-500">General analysis</div>
            </div>
          </button>

          <div className="border-t border-slate-800 my-2" />

          {agents.map(a => (
            <button key={a.id} onClick={() => startSession(a.id, 'agent')}
              className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-slate-800 transition-colors mb-1 text-left">
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
                style={{ backgroundColor: a.avatar_color }}>
                {a.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
              </div>
              <div>
                <div className="text-xs font-medium">{a.name}</div>
                <div className="text-xs text-slate-500">{a.role}</div>
              </div>
            </button>
          ))}

          {sessions.length > 0 && (
            <>
              <div className="border-t border-slate-800 my-2" />
              <h4 className="text-xs text-slate-500 mb-2">Previous Sessions</h4>
              {sessions.map(s => (
                <button key={s.id} onClick={() => selectSession(s)}
                  className="w-full text-left p-2 rounded-lg hover:bg-slate-800 transition-colors mb-1 text-xs">
                  <div className="font-medium">{s.agent_name || 'Analyst'}</div>
                  <div className="text-slate-500">{s.message_count} messages</div>
                </button>
              ))}
            </>
          )}
        </div>

        {/* Chat Area */}
        <div className="lg:col-span-3 card flex flex-col">
          {activeSession ? (
            <>
              <div className="border-b border-slate-800 pb-3 mb-3">
                <div className="text-sm font-medium">
                  {activeSession.agent_name || 'Analysis Agent'}
                </div>
                <div className="text-xs text-slate-500">{activeSession.session_type} session</div>
              </div>

              <div className="flex-1 overflow-y-auto space-y-3 mb-3">
                {messages.map(m => (
                  <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm ${
                      m.role === 'user'
                        ? 'bg-brand-600 text-white'
                        : 'bg-slate-800 text-slate-200'
                    }`}>
                      {m.content}
                    </div>
                  </div>
                ))}
                {sending && (
                  <div className="flex justify-start">
                    <div className="bg-slate-800 rounded-lg px-4 py-2.5">
                      <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
                    </div>
                  </div>
                )}
                <div ref={chatEnd} />
              </div>

              <div className="flex gap-2">
                <input
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
                  placeholder="Ask the agent..."
                  className="input flex-1"
                  disabled={sending}
                />
                <button onClick={send} disabled={sending || !input.trim()} className="btn-primary px-3 disabled:opacity-50">
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-600 text-sm">
              Select an agent to start a conversation
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
