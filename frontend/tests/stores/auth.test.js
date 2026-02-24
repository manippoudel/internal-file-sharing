/**
 * Tests for auth store
 *
 * Tests cover:
 * - Login stores token in localStorage
 * - Login sets user state
 * - Logout clears token and state
 * - isAuthenticated getter
 * - isAdmin getter
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../../src/stores/auth'
import axios from 'axios'

// Mock axios
vi.mock('axios')

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('should initialize with default state', () => {
    const store = useAuthStore()

    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('should login and store token', async () => {
    const store = useAuthStore()
    const mockResponse = {
      data: {
        token: 'test-token-123',
        user: {
          id: '1',
          username: 'testuser',
          email: 'test@example.com',
          role: 'user',
        },
      },
    }

    axios.post.mockResolvedValueOnce(mockResponse)

    await store.login('testuser', 'password123')

    expect(store.token).toBe('test-token-123')
    expect(store.user).toEqual(mockResponse.data.user)
    expect(localStorage.getItem).toHaveBeenCalledWith('token')
    expect(localStorage.setItem).toHaveBeenCalledWith('token', 'test-token-123')
  })

  it('should handle login failure', async () => {
    const store = useAuthStore()
    const errorMessage = 'Invalid credentials'

    axios.post.mockRejectedValueOnce({
      response: { data: { detail: errorMessage } },
    })

    await store.login('testuser', 'wrongpassword')

    expect(store.error).toBeTruthy()
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
  })

  it('should logout and clear state', async () => {
    const store = useAuthStore()

    // Set some state
    store.token = 'test-token'
    store.user = { id: '1', username: 'testuser' }

    axios.post.mockResolvedValueOnce({ data: { message: 'Logged out' } })

    await store.logout()

    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(localStorage.removeItem).toHaveBeenCalledWith('token')
  })

  it('should have isAuthenticated getter return true when token exists', () => {
    const store = useAuthStore()

    expect(store.isAuthenticated).toBe(false)

    store.token = 'test-token'

    expect(store.isAuthenticated).toBe(true)
  })

  it('should have isAdmin getter return true for admin users', () => {
    const store = useAuthStore()

    expect(store.isAdmin).toBe(false)

    store.user = { id: '1', username: 'admin', role: 'admin' }

    expect(store.isAdmin).toBe(true)
  })

  it('should have isAdmin getter return false for regular users', () => {
    const store = useAuthStore()

    store.user = { id: '1', username: 'user', role: 'user' }

    expect(store.isAdmin).toBe(false)
  })

  it('should fetch current user', async () => {
    const store = useAuthStore()
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      role: 'user',
    }

    axios.get.mockResolvedValueOnce({ data: mockUser })

    await store.fetchCurrentUser()

    expect(store.user).toEqual(mockUser)
  })

  it('should change password successfully', async () => {
    const store = useAuthStore()

    axios.post.mockResolvedValueOnce({
      data: { message: 'Password changed successfully' },
    })

    await store.changePassword('oldpass', 'newpass')

    expect(axios.post).toHaveBeenCalledWith(
      '/api/v1/auth/change-password',
      expect.objectContaining({
        old_password: 'oldpass',
        new_password: 'newpass',
      })
    )
  })

  it('should restore token from localStorage on init', () => {
    localStorage.setItem('token', 'stored-token')

    const store = useAuthStore()
    store.initializeAuth()

    expect(store.token).toBe('stored-token')
  })
})
