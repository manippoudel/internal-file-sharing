/**
 * Vitest global setup
 * Runs before all tests
 */

import { vi } from 'vitest'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn((key) => {
    return localStorageMock.store[key] || null
  }),
  setItem: vi.fn((key, value) => {
    localStorageMock.store[key] = value.toString()
  }),
  removeItem: vi.fn((key) => {
    delete localStorageMock.store[key]
  }),
  clear: vi.fn(() => {
    localStorageMock.store = {}
  }),
  store: {},
}

global.localStorage = localStorageMock

// Mock console methods to reduce test output noise
global.console = {
  ...console,
  error: vi.fn(),
  warn: vi.fn(),
}

// Reset mocks before each test
beforeEach(() => {
  localStorageMock.store = {}
  vi.clearAllMocks()
})
