import { useState } from 'react'
import { useLLM, LLM_PROVIDERS } from '../../lib/llmContext'
import { KeyRound, X, Check } from 'lucide-react'

export default function ApiKeyBanner() {
  const { hasActiveKey, activeProvider, setKey } = useLLM()
  const [dismissed, setDismissed] = useState(false)
  const [input, setInput] = useState('')
  const [saved, setSaved] = useState(false)

  if (hasActiveKey || dismissed) return null

  const provider = LLM_PROVIDERS.find(p => p.id === activeProvider)

  const save = () => {
    if (!input.trim()) return
    setKey(activeProvider, input.trim())
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="px-6 py-3 flex items-center gap-4"
      style={{ background: 'rgba(200,169,110,0.08)', borderBottom: '1px solid rgba(200,169,110,0.15)' }}>
      <KeyRound className="w-4 h-4 text-gold-500 flex-shrink-0" />
      <span className="text-sm text-navy-500">
        Add your <strong className="text-navy-700">{provider?.name}</strong> API key to enable AI-powered predictions
      </span>
      <input
        type="password"
        value={input}
        onChange={e => setInput(e.target.value)}
        placeholder={`${provider?.prefix || ''}...`}
        className="input flex-1 max-w-xs text-xs"
        onKeyDown={e => e.key === 'Enter' && save()}
      />
      <button onClick={save} className="btn-primary text-xs px-4 py-2 flex items-center gap-1">
        {saved ? <Check className="w-3 h-3" /> : null}
        {saved ? 'Saved' : 'Save'}
      </button>
      <button onClick={() => setDismissed(true)} className="text-navy-300 hover:text-navy-600 transition-colors">
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}
