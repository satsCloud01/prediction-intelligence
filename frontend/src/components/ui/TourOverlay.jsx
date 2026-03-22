import { useEffect, useRef, useState, useCallback } from 'react'
import { X, ChevronLeft, ChevronRight, Lightbulb, MousePointerClick } from 'lucide-react'

export default function TourOverlay({ step, currentStep, totalSteps, onNext, onPrev, onClose }) {
  const tooltipRef = useRef(null)
  const [pos, setPos] = useState({ top: 0, left: 0, width: 0, height: 0 })
  const [placement, setPlacement] = useState('below')

  const measure = useCallback(() => {
    if (!step?.target) return
    const el = document.querySelector(step.target)
    if (!el) return

    const rect = el.getBoundingClientRect()
    const pad = 8
    const newPos = {
      top: rect.top + window.scrollY - pad,
      left: rect.left - pad,
      width: rect.width + pad * 2,
      height: rect.height + pad * 2,
    }
    setPos(newPos)

    // Decide placement: if target is in top half, tooltip goes below; else above
    const targetMid = rect.top + rect.height / 2
    setPlacement(targetMid < window.innerHeight * 0.5 ? 'below' : 'above')
  }, [step])

  useEffect(() => {
    if (!step?.target) return
    const el = document.querySelector(step.target)
    if (!el) return

    el.scrollIntoView({ behavior: 'smooth', block: 'center' })

    const timer = setTimeout(measure, 400)
    return () => clearTimeout(timer)
  }, [step, measure])

  // Reposition on scroll/resize
  useEffect(() => {
    if (!step?.target) return
    const handler = () => measure()
    window.addEventListener('scroll', handler, true)
    window.addEventListener('resize', handler)
    return () => {
      window.removeEventListener('scroll', handler, true)
      window.removeEventListener('resize', handler)
    }
  }, [step, measure])

  if (!step) return null

  const tooltipStyle = placement === 'below'
    ? { top: pos.top + pos.height + 16, left: Math.max(16, Math.min(pos.left, window.innerWidth - 420)) }
    : { top: pos.top - 16, left: Math.max(16, Math.min(pos.left, window.innerWidth - 420)), transform: 'translateY(-100%)' }

  return (
    <div className="fixed inset-0 z-[9999]">
      {/* SVG mask overlay with cutout */}
      <svg className="absolute inset-0 w-full h-full" style={{ pointerEvents: 'none' }}>
        <defs>
          <mask id="tour-mask">
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            <rect
              x={pos.left}
              y={pos.top - window.scrollY}
              width={pos.width}
              height={pos.height}
              rx="8"
              fill="black"
            />
          </mask>
        </defs>
        <rect
          x="0" y="0" width="100%" height="100%"
          fill="rgba(0,0,0,0.6)"
          mask="url(#tour-mask)"
          style={{ pointerEvents: 'all', cursor: 'default' }}
          onClick={onClose}
        />
      </svg>

      {/* Highlight ring around target */}
      <div
        className="absolute rounded-lg pointer-events-none"
        style={{
          top: pos.top - window.scrollY,
          left: pos.left,
          width: pos.width,
          height: pos.height,
          border: '2px solid #c8a96e',
          boxShadow: '0 0 0 4px rgba(200,169,110,0.25), 0 0 20px rgba(200,169,110,0.15)',
        }}
      />

      {/* Tooltip card */}
      <div
        ref={tooltipRef}
        className="absolute z-[10000] rounded-xl shadow-2xl max-w-md"
        style={{
          ...tooltipStyle,
          top: placement === 'below'
            ? pos.top - window.scrollY + pos.height + 16
            : pos.top - window.scrollY - 16,
          background: '#ffffff',
          border: '1px solid rgba(21,32,64,0.12)',
          borderTop: '3px solid #c8a96e',
          padding: '20px',
        }}
      >
        {/* Step counter + close */}
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold" style={{ color: '#c8a96e' }}>
            Step {currentStep + 1} of {totalSteps}
          </span>
          <button
            onClick={onClose}
            className="hover:opacity-70 transition-opacity"
            style={{ color: '#8a93a6' }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Title + content */}
        <h3 className="text-lg font-bold mb-2" style={{ color: '#152040', fontFamily: "'Playfair Display', serif" }}>
          {step.title}
        </h3>
        <p className="text-sm leading-relaxed mb-3" style={{ color: '#4a5568' }}>
          {step.content}
        </p>

        {/* Try This Example */}
        {step.example && (
          <div
            className="rounded-lg p-3 mb-3"
            style={{ background: 'rgba(200,169,110,0.08)', border: '1px solid rgba(200,169,110,0.2)' }}
          >
            <div className="flex items-center gap-1.5 text-xs font-semibold mb-1" style={{ color: '#b8942e' }}>
              <MousePointerClick size={12} /> Try This Example
            </div>
            <p className="text-xs" style={{ color: '#4a5568' }}>{step.example}</p>
          </div>
        )}

        {/* Pro Tip */}
        {step.proTip && (
          <div
            className="rounded-lg p-3 mb-3"
            style={{ background: 'rgba(21,32,64,0.04)', border: '1px solid rgba(21,32,64,0.1)' }}
          >
            <div className="flex items-center gap-1.5 text-xs font-semibold mb-1" style={{ color: '#2563eb' }}>
              <Lightbulb size={12} /> Pro Tip
            </div>
            <p className="text-xs" style={{ color: '#4a5568' }}>{step.proTip}</p>
          </div>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={onPrev}
            disabled={currentStep === 0}
            className="flex items-center gap-1 text-sm transition-colors disabled:opacity-30"
            style={{ color: '#8a93a6' }}
          >
            <ChevronLeft size={16} /> Back
          </button>

          {/* Progress dots */}
          <div className="flex gap-1.5">
            {Array.from({ length: totalSteps }).map((_, i) => (
              <div
                key={i}
                className="w-2 h-2 rounded-full transition-colors"
                style={{
                  background: i === currentStep
                    ? '#c8a96e'
                    : i < currentStep
                      ? 'rgba(200,169,110,0.4)'
                      : 'rgba(21,32,64,0.12)',
                }}
              />
            ))}
          </div>

          <button
            onClick={onNext}
            className="flex items-center gap-1 text-sm font-medium transition-colors"
            style={{ color: '#c8a96e' }}
          >
            {currentStep === totalSteps - 1 ? 'Finish' : 'Next'} <ChevronRight size={16} />
          </button>
        </div>

        {/* Skip */}
        {currentStep < totalSteps - 1 && (
          <div className="text-center mt-3">
            <button
              onClick={onClose}
              className="text-xs hover:underline transition-colors"
              style={{ color: '#8a93a6' }}
            >
              Skip Tour
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
