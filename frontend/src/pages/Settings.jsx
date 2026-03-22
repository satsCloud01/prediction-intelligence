import { useState } from 'react'
import { useLLM, LLM_PROVIDERS } from '../lib/llmContext'
import { api } from '../lib/api'
import {
  Settings as SettingsIcon, KeyRound, Check, Eye, EyeOff, Loader2,
  Trash2, Zap, Brain, Globe, Cloud, Cpu, Server, Wifi,
} from 'lucide-react'

const PROVIDER_ICONS = {
  anthropic: Brain,
  openai: Zap,
  google: Globe,
  mistral: Cloud,
  groq: Cpu,
  together: Server,
  ollama: Wifi,
}

const PROVIDER_COLORS = {
  anthropic: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  openai: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  google: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  mistral: 'text-violet-400 bg-violet-500/10 border-violet-500/20',
  groq: 'text-pink-400 bg-pink-500/10 border-pink-500/20',
  together: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  ollama: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
}

export default function Settings() {
  const { keys, setKey, clearKey, activeProvider, setActiveProvider, activeModel, setActiveModel } = useLLM()
  const [inputs, setInputs] = useState(() => {
    const obj = {}
    LLM_PROVIDERS.forEach(p => { obj[p.id] = keys[p.id] ? '••••••••••••••••' : '' })
    return obj
  })
  const [visible, setVisible] = useState({})
  const [saved, setSaved] = useState({})
  const [testing, setTesting] = useState({})
  const [testResult, setTestResult] = useState({})
  const [providerModels, setProviderModels] = useState(null)

  const saveKey = (provider) => {
    const val = inputs[provider]
    if (!val.trim() || val === '••••••••••••••••') return
    setKey(provider, val.trim())
    setSaved(prev => ({ ...prev, [provider]: true }))
    setInputs(prev => ({ ...prev, [provider]: '••••••••••••••••' }))
    setTimeout(() => setSaved(prev => ({ ...prev, [provider]: false })), 2000)
  }

  const removeKey = (provider) => {
    clearKey(provider)
    setInputs(prev => ({ ...prev, [provider]: '' }))
  }

  const testKey = async (provider) => {
    const key = keys[provider]
    if (!key) return
    setTesting(prev => ({ ...prev, [provider]: true }))
    try {
      const result = await api.settings.testKey(provider, key)
      setTestResult(prev => ({ ...prev, [provider]: result }))
    } catch (err) {
      setTestResult(prev => ({ ...prev, [provider]: { success: false, message: err.message } }))
    }
    setTesting(prev => ({ ...prev, [provider]: false }))
  }

  const toggleVisible = (provider) => {
    setVisible(prev => ({ ...prev, [provider]: !prev[provider] }))
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-brand-400" /> Settings
        </h1>
        <p className="text-sm text-slate-500">Configure LLM providers and preferences</p>
      </div>

      {/* Active Provider Selection */}
      <div className="card mb-6">
        <h3 className="text-sm font-semibold mb-3">Active Provider</h3>
        <p className="text-xs text-slate-500 mb-4">Select which LLM provider to use for AI-powered features</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
          {LLM_PROVIDERS.map(p => {
            const Icon = PROVIDER_ICONS[p.id] || Brain
            const isActive = activeProvider === p.id
            const hasKey = keys[p.id]?.length > 0 || p.id === 'ollama'
            return (
              <button key={p.id} onClick={() => setActiveProvider(p.id)}
                className={`p-3 rounded-lg border text-center transition-all ${
                  isActive
                    ? 'border-brand-500 bg-brand-500/10'
                    : 'border-slate-800 hover:border-slate-700'
                }`}>
                <Icon className={`w-5 h-5 mx-auto mb-1 ${isActive ? 'text-brand-400' : 'text-slate-500'}`} />
                <div className={`text-xs font-medium ${isActive ? 'text-brand-300' : 'text-slate-400'}`}>{p.name}</div>
                {hasKey && <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 mx-auto mt-1" />}
              </button>
            )
          })}
        </div>
      </div>

      {/* API Keys */}
      <div className="card mb-6">
        <h3 className="text-sm font-semibold mb-1">API Keys</h3>
        <p className="text-xs text-slate-500 mb-4">Keys are stored only in your browser's localStorage — never sent to our server for storage</p>

        <div className="space-y-4">
          {LLM_PROVIDERS.map(p => {
            const Icon = PROVIDER_ICONS[p.id] || Brain
            const colors = PROVIDER_COLORS[p.id] || PROVIDER_COLORS.anthropic
            const hasKey = keys[p.id]?.length > 0
            const result = testResult[p.id]

            return (
              <div key={p.id} className={`p-4 rounded-lg border ${
                activeProvider === p.id ? 'border-brand-500/30 bg-brand-500/5' : 'border-slate-800'
              }`}>
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-8 h-8 rounded-lg border flex items-center justify-center ${colors}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-medium">{p.name}</div>
                    <div className="text-xs text-slate-500">{p.desc}</div>
                  </div>
                  {hasKey && <div className="ml-auto badge bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Configured</div>}
                </div>

                {p.id === 'ollama' ? (
                  <div className="text-xs text-slate-500">
                    Ollama runs locally — no API key needed. Ensure Ollama is running at localhost:11434.
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <input
                        type={visible[p.id] ? 'text' : 'password'}
                        value={inputs[p.id]}
                        onChange={e => setInputs(prev => ({ ...prev, [p.id]: e.target.value }))}
                        placeholder={`${p.prefix}...`}
                        className="input w-full pr-8 text-xs"
                        onKeyDown={e => e.key === 'Enter' && saveKey(p.id)}
                      />
                      <button onClick={() => toggleVisible(p.id)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                        {visible[p.id] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <button onClick={() => saveKey(p.id)}
                      className="btn-primary text-xs px-3 flex items-center gap-1">
                      {saved[p.id] ? <Check className="w-3 h-3" /> : <KeyRound className="w-3 h-3" />}
                      {saved[p.id] ? 'Saved' : 'Save'}
                    </button>
                    {hasKey && (
                      <>
                        <button onClick={() => testKey(p.id)} disabled={testing[p.id]}
                          className="btn-outline text-xs px-3 flex items-center gap-1 disabled:opacity-50">
                          {testing[p.id] ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
                          Test
                        </button>
                        <button onClick={() => removeKey(p.id)} className="text-slate-600 hover:text-red-400 px-2">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </>
                    )}
                  </div>
                )}

                {result && (
                  <div className={`mt-2 text-xs p-2 rounded ${
                    result.success ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                  }`}>
                    {result.message}
                    {result.latency_ms && <span className="ml-2 text-slate-500">({result.latency_ms}ms)</span>}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Platform Info */}
      <div className="card">
        <h3 className="text-sm font-semibold mb-3">About PredictionIntelligence</h3>
        <div className="grid grid-cols-2 gap-3 text-xs">
          {[
            ['Platform', 'PredictionIntelligence v1.0'],
            ['Frontend', 'React 18 + Vite + Tailwind CSS'],
            ['Backend', 'FastAPI + SQLAlchemy + SQLite'],
            ['Visualization', 'Recharts + React Flow'],
            ['AI Engine', 'Universal LLM Dispatcher (7 providers)'],
            ['Architecture', 'Swarm Intelligence 5-Stage Pipeline'],
          ].map(([k, v]) => (
            <div key={k}>
              <span className="text-slate-500">{k}:</span>{' '}
              <span className="text-slate-300">{v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
