import { useState, useCallback } from 'react'

export default function useTour(tourKey, steps) {
  const storageKey = `pi_tour_${tourKey}`
  const [currentStep, setCurrentStep] = useState(0)
  const [isActive, setIsActive] = useState(false)
  const [hasCompleted, setHasCompleted] = useState(
    () => localStorage.getItem(storageKey) === 'done'
  )

  const start = useCallback(() => {
    setCurrentStep(0)
    setIsActive(true)
  }, [])

  const next = useCallback(() => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1)
    } else {
      finish()
    }
  }, [currentStep, steps.length])

  const prev = useCallback(() => {
    if (currentStep > 0) setCurrentStep(prev => prev - 1)
  }, [currentStep])

  const finish = useCallback(() => {
    setIsActive(false)
    setHasCompleted(true)
    localStorage.setItem(storageKey, 'done')
  }, [storageKey])

  const reset = useCallback(() => {
    localStorage.removeItem(storageKey)
    setHasCompleted(false)
    setCurrentStep(0)
  }, [storageKey])

  return {
    currentStep,
    isActive,
    hasCompleted,
    step: isActive ? steps[currentStep] : null,
    totalSteps: steps.length,
    start,
    next,
    prev,
    finish,
    reset,
  }
}
