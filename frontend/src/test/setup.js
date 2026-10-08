import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

beforeEach(() => {
  // jsdom implements neither object URLs nor scrolling.
  window.scrollTo = vi.fn()
  let next = 0
  URL.createObjectURL = vi.fn(() => `blob:mock-${++next}`)
  URL.revokeObjectURL = vi.fn()
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.useRealTimers()
})
