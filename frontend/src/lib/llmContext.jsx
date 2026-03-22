/**
 * LLM Context — API keys are NEVER persisted (no localStorage).
 * Keys live in React state only — cleared on page refresh.
 * Users are always prompted via UI to enter keys.
 */
import { createContext, useContext, useState, useCallback } from 'react'

const LLMContext = createContext()

export const LLM_PROVIDERS = [
  { id: 'anthropic', name: 'Anthropic', desc: 'Claude models (Haiku, Sonnet)', prefix: 'sk-ant-' },
  { id: 'openai', name: 'OpenAI', desc: 'GPT models (4o-mini, 4o)', prefix: 'sk-' },
  { id: 'google', name: 'Google', desc: 'Gemini models (Flash, Pro)', prefix: 'AI' },
  { id: 'mistral', name: 'Mistral', desc: 'Mistral models (Small, Large)', prefix: '' },
  { id: 'groq', name: 'Groq', desc: 'Fast inference (Llama, Mixtral)', prefix: 'gsk_' },
  { id: 'together', name: 'Together', desc: 'Open models (Llama, Qwen)', prefix: '' },
  { id: 'ollama', name: 'Ollama', desc: 'Local models (no key needed)', prefix: '' },
]

// Module-level state for api.js to read (no localStorage)
let _activeKey = ''
let _activeProvider = 'anthropic'
let _activeModel = ''

export function LLMProvider({ children }) {
  const [keys, setKeys] = useState(() => {
    const obj = {}
    LLM_PROVIDERS.forEach(p => { obj[p.id] = '' })
    return obj
  })
  const [activeProvider, setActiveProviderState] = useState('anthropic')
  const [activeModel, setActiveModelState] = useState('')

  const setKey = useCallback((provider, key) => {
    const trimmed = key.trim()
    setKeys(prev => {
      const next = { ...prev, [provider]: trimmed }
      // Update module-level ref for api.js
      if (provider === _activeProvider) _activeKey = trimmed
      return next
    })
  }, [])

  const clearKey = useCallback((provider) => {
    setKeys(prev => {
      const next = { ...prev, [provider]: '' }
      if (provider === _activeProvider) _activeKey = ''
      return next
    })
  }, [])

  const setActiveProvider = useCallback((p) => {
    setActiveProviderState(p)
    _activeProvider = p
    setKeys(prev => {
      _activeKey = prev[p] || ''
      return prev
    })
  }, [])

  const setActiveModel = useCallback((m) => {
    setActiveModelState(m)
    _activeModel = m
  }, [])

  const getActiveKey = useCallback(() => keys[activeProvider] || '', [keys, activeProvider])
  const hasActiveKey = (keys[activeProvider]?.length > 0) || activeProvider === 'ollama'

  // Keep module-level in sync
  _activeProvider = activeProvider
  _activeKey = keys[activeProvider] || ''
  _activeModel = activeModel

  return (
    <LLMContext.Provider value={{
      keys, setKey, clearKey,
      activeProvider, setActiveProvider,
      activeModel, setActiveModel,
      getActiveKey, hasActiveKey,
    }}>
      {children}
    </LLMContext.Provider>
  )
}

export const useLLM = () => useContext(LLMContext)

// These are read by api.js — they use module-level state (NOT localStorage)
export function getStoredKey() { return _activeKey }
export function getStoredProvider() { return _activeProvider }
export function getStoredModel() { return _activeModel }
