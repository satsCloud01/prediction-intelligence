import { useState, useCallback, useRef } from 'react'

export default function useTour(tourKey, steps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [isActive, setIsActive] = useState(false)
  const stepsRef = useRef(steps)
  stepsRef.current = steps

  const start = useCallback(() => {
    setCurrentStep(0)
    setIsActive(true)
  }, [])

  const finish = useCallback(() => {
    setIsActive(false)
    setCurrentStep(0)
  }, [])

  const next = useCallback(() => {
    setCurrentStep(prev => {
      if (prev < stepsRef.current.length - 1) return prev + 1
      // Last step — finish
      setTimeout(() => setIsActive(false), 0)
      return 0
    })
  }, [])

  const prev = useCallback(() => {
    setCurrentStep(prev => prev > 0 ? prev - 1 : prev)
  }, [])

  return {
    currentStep,
    isActive,
    step: isActive ? steps[currentStep] : null,
    totalSteps: steps.length,
    start,
    next,
    prev,
    finish,
  }
}
