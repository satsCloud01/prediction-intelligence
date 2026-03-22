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
    window.addEventListener('scroll', measure, true)
    window.addEventListener('resize', measure)
    return () => { window.removeEventListener('scroll', measure, true); window.removeEventListener('resize', measure) }
  }, [step, measure])

  // Prevent body scroll while tour is active
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  if (!step) return null

  const pad = 10
  const cutout = rect ? {
    x: rect.left - pad,
    y: rect.top - pad,
    w: rect.width + pad * 2,
    h: rect.height + pad * 2,
  } : null

  const placement = rect && rect.top > window.innerHeight * 0.5 ? 'above' : 'below'
  const ttTop = cutout
    ? placement === 'below' ? cutout.y + cutout.h + 16 : cutout.y - 16
    : window.innerHeight / 2 - 150
  const ttLeft = cutout
    ? Math.max(16, Math.min(cutout.x, window.innerWidth - 420))
    : Math.max(16, window.innerWidth / 2 - 200)

  const overlay = (
    <div
      style={{ position: 'fixed', inset: 0, zIndex: 100000 }}
      onMouseDown={e => e.stopPropagation()}
      onClick={e => e.stopPropagation()}
    >
      {/* Dark backdrop with cutout */}
      <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <mask id="tour-mask-v2">
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            {cutout && <rect x={cutout.x} y={cutout.y} width={cutout.w} height={cutout.h} rx="10" fill="black" />}
          </mask>
        </defs>
        <rect x="0" y="0" width="100%" height="100%" fill="rgba(0,0,0,0.55)" mask="url(#tour-mask-v2)" />
      </svg>

      {/* Gold highlight ring */}
      {cutout && (
        <div style={{
          position: 'absolute', top: cutout.y, left: cutout.x,
          width: cutout.w, height: cutout.h, borderRadius: 10,
          border: '2px solid #c8a96e',
          boxShadow: '0 0 0 4px rgba(200,169,110,0.2), 0 0 24px rgba(200,169,110,0.12)',
          pointerEvents: 'none',
        }} />
      )}

      {/* Tooltip */}
      <div
        style={{
          position: 'absolute',
          top: ttTop,
          left: ttLeft,
          transform: placement === 'above' ? 'translateY(-100%)' : undefined,
          width: 400,
          maxWidth: 'calc(100vw - 32px)',
          background: '#fff',
          border: '1px solid rgba(21,32,64,0.12)',
          borderTop: '3px solid #c8a96e',
          borderRadius: 12,
          padding: 20,
          boxShadow: '0 12px 40px rgba(0,0,0,0.15)',
          zIndex: 100001,
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: '#c8a96e', letterSpacing: 1 }}>
            STEP {currentStep + 1} OF {totalSteps}
          </span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#8a93a6', padding: 4 }}>
            <X size={16} />
          </button>
        </div>

        {/* Title */}
        <h3 style={{ fontSize: 18, fontWeight: 700, color: '#152040', fontFamily: "'Playfair Display', serif", marginBottom: 8 }}>
          {step.title}
        </h3>
        <p style={{ fontSize: 14, lineHeight: 1.6, color: '#4a5568', marginBottom: 12 }}>
          {step.content}
        </p>

        {/* Try This */}
        {step.example && (
          <div style={{ background: 'rgba(200,169,110,0.08)', border: '1px solid rgba(200,169,110,0.2)', borderRadius: 8, padding: 12, marginBottom: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 700, color: '#b8942e', marginBottom: 4 }}>
              <MousePointerClick size={12} /> TRY THIS EXAMPLE
            </div>
            <p style={{ fontSize: 12, color: '#4a5568', margin: 0 }}>{step.example}</p>
          </div>
        )}

        {/* Pro Tip */}
        {step.proTip && (
          <div style={{ background: 'rgba(21,32,64,0.04)', border: '1px solid rgba(21,32,64,0.1)', borderRadius: 8, padding: 12, marginBottom: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 700, color: '#2563eb', marginBottom: 4 }}>
              <Lightbulb size={12} /> PRO TIP
            </div>
            <p style={{ fontSize: 12, color: '#4a5568', margin: 0 }}>{step.proTip}</p>
          </div>
        )}

        {/* Nav */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
          <button
            onClick={onPrev}
            disabled={currentStep === 0}
            style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, color: currentStep === 0 ? '#ccc' : '#8a93a6', background: 'none', border: 'none', cursor: currentStep === 0 ? 'default' : 'pointer' }}
          >
            <ChevronLeft size={16} /> Back
          </button>

          {/* Dots */}
          <div style={{ display: 'flex', gap: 5 }}>
            {Array.from({ length: totalSteps }).map((_, i) => (
              <div key={i} style={{
                width: 7, height: 7, borderRadius: '50%',
                background: i === currentStep ? '#c8a96e' : i < currentStep ? 'rgba(200,169,110,0.4)' : 'rgba(21,32,64,0.12)',
              }} />
            ))}
          </div>

          <button
            onClick={onNext}
            style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, fontWeight: 600, color: '#c8a96e', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            {currentStep === totalSteps - 1 ? 'Finish' : 'Next'} <ChevronRight size={16} />
          </button>
        </div>

        {/* Skip */}
        {currentStep < totalSteps - 1 && (
          <div style={{ textAlign: 'center', marginTop: 10 }}>
            <button onClick={onClose} style={{ fontSize: 11, color: '#8a93a6', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
              Skip Tour
            </button>
          </div>
        )}
      </div>
    </div>
  )

  return createPortal(overlay, document.body)
}
