import { defineStore } from 'pinia'
import authService from '../services/authService'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('auth_token') || null,
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    mustChangePassword: (state) => state.user?.must_change_password || false
  },

  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null
      
      try {
        const response = await authService.login(username, password)
        
        if (response.success) {
          this.token = response.token
          this.user = {
            id: response.user_id,
            username: response.username,
            role: response.role,
            must_change_password: response.must_change_password
          }
          localStorage.setItem('auth_token', response.token)
          return true
        } else {
          this.error = response.message || 'Login failed'
          return false
        }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Login failed'
        return false
      } finally {
        this.loading = false
      }
    },

    async logout() {
      try {
        await authService.logout()
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        this.token = null
        this.user = null
        localStorage.removeItem('auth_token')
      }
    },

    async fetchCurrentUser() {
      if (!this.token) return
      
      try {
        this.user = await authService.getCurrentUser()
      } catch (error) {
        console.error('Failed to fetch current user:', error)
        this.logout()
      }
    },

    async changePassword(oldPassword, newPassword) {
      this.loading = true
      this.error = null
      
      try {
        const response = await authService.changePassword(oldPassword, newPassword)
        
        if (response.success) {
          if (this.user) {
            this.user.must_change_password = false
          }
          return true
        } else {
          this.error = response.message || 'Password change failed'
          return false
        }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Password change failed'
        return false
      } finally {
        this.loading = false
      }
    }
  }
})
