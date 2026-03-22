import { useEffect, useState, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { X, ChevronLeft, ChevronRight, Lightbulb, MousePointerClick } from 'lucide-react'

export default function TourOverlay({ step, currentStep, totalSteps, onNext, onPrev, onClose }) {
  const [rect, setRect] = useState(null)

  const measure = useCallback(() => {
    if (!step?.target) { setRect(null); return }
    const el = document.querySelector(step.target)
    if (!el) { setRect(null); return }
    const r = el.getBoundingClientRect()
    setRect({ top: r.top, left: r.left, width: r.width, height: r.height })
  }, [step])

  useEffect(() => {
    if (!step?.target) return
    const el = document.querySelector(step.target)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    const t = setTimeout(measure, 500)
    return () => clearTimeout(t)
  }, [step, measure])

  useEffect(() => {
    if (!step) return
    const h = () => measure()
    window.addEventListener('scroll', h, true)
    window.addEventListener('resize', h)
    return () => { window.removeEventListener('scroll', h, true); window.removeEventListener('resize', h) }
  }, [step, measure])

  if (!step) return null

  const pad = 10
  const cx = rect ? rect.left - pad : 0
  const cy = rect ? rect.top - pad : 0
  const cw = rect ? rect.width + pad * 2 : 0
  const ch = rect ? rect.height + pad * 2 : 0

  const below = !rect || rect.top < window.innerHeight * 0.5
  const ttTop = rect ? (below ? cy + ch + 16 : cy - 16) : window.innerHeight / 3
  const ttLeft = rect ? Math.max(16, Math.min(cx, window.innerWidth - 420)) : 40

  return createPortal(
    <div id="pi-tour-root" style={{ position: 'fixed', inset: 0, zIndex: 2147483647, pointerEvents: 'auto' }}>
      {/* Backdrop */}
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.55)' }} />

      {/* Cutout - make target area visible */}
      {rect && (
        <div style={{
          position: 'absolute', top: cy, left: cx, width: cw, height: ch,
          borderRadius: 10, border: '2px solid #c8a96e',
          boxShadow: '0 0 0 9999px rgba(0,0,0,0.55), 0 0 0 4px rgba(200,169,110,0.25)',
          background: 'transparent',
          pointerEvents: 'none',
        }} />
      )}

      {/* Tooltip */}
      <div style={{
        position: 'absolute',
        top: ttTop, left: ttLeft,
        transform: !below ? 'translateY(-100%)' : undefined,
        width: 400, maxWidth: 'calc(100vw - 32px)',
        background: '#fff', borderRadius: 12,
        border: '1px solid rgba(21,32,64,0.12)', borderTop: '3px solid #c8a96e',
        padding: 20, boxShadow: '0 12px 40px rgba(0,0,0,0.18)',
        pointerEvents: 'auto',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: '#c8a96e', letterSpacing: 1, textTransform: 'uppercase' }}>
            Step {currentStep + 1} of {totalSteps}
          </span>
          <button onClick={e => { e.stopPropagation(); onClose() }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#8a93a6', padding: 4 }}>
            <X size={16} />
          </button>
        </div>

        <h3 style={{ fontSize: 18, fontWeight: 700, color: '#152040', fontFamily: "'Playfair Display',serif", marginBottom: 8, marginTop: 0 }}>
          {step.title}
        </h3>
        <p style={{ fontSize: 14, lineHeight: 1.6, color: '#4a5568', marginBottom: 12 }}>
          {step.content}
        </p>

        {step.example && (
          <div style={{ background: 'rgba(200,169,110,0.08)', border: '1px solid rgba(200,169,110,0.2)', borderRadius: 8, padding: 12, marginBottom: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 700, color: '#b8942e', marginBottom: 4 }}>
              <MousePointerClick size={12} /> TRY THIS EXAMPLE
            </div>
            <p style={{ fontSize: 12, color: '#4a5568', margin: 0 }}>{step.example}</p>
          </div>
        )}

        {step.proTip && (
          <div style={{ background: 'rgba(21,32,64,0.04)', border: '1px solid rgba(21,32,64,0.1)', borderRadius: 8, padding: 12, marginBottom: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 700, color: '#2563eb', marginBottom: 4 }}>
              <Lightbulb size={12} /> PRO TIP
            </div>
            <p style={{ fontSize: 12, color: '#4a5568', margin: 0 }}>{step.proTip}</p>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
          <button onClick={e => { e.stopPropagation(); onPrev() }} disabled={currentStep === 0}
            style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, color: currentStep === 0 ? '#ccc' : '#8a93a6', background: 'none', border: 'none', cursor: currentStep === 0 ? 'default' : 'pointer' }}>
            <ChevronLeft size={16} /> Back
          </button>
          <div style={{ display: 'flex', gap: 5 }}>
            {Array.from({ length: Math.min(totalSteps, 17) }).map((_, i) => (
              <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: i === currentStep ? '#c8a96e' : i < currentStep ? 'rgba(200,169,110,0.4)' : 'rgba(21,32,64,0.12)' }} />
            ))}
          </div>
          <button onClick={e => { e.stopPropagation(); onNext() }}
            style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, fontWeight: 600, color: '#c8a96e', background: 'none', border: 'none', cursor: 'pointer' }}>
            {currentStep === totalSteps - 1 ? 'Finish' : 'Next'} <ChevronRight size={16} />
          </button>
        </div>

        {currentStep < totalSteps - 1 && (
          <div style={{ textAlign: 'center', marginTop: 10 }}>
            <button onClick={e => { e.stopPropagation(); onClose() }}
              style={{ fontSize: 11, color: '#8a93a6', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
              Skip Tour
            </button>
          </div>
        )}
      </div>
    </div>,
    document.body
  )
}
