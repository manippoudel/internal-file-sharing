import apiClient from './api'

export default {
  async login(username, password) {
    const response = await apiClient.post('/auth/login', { username, password })
    return response.data
  },

  async logout() {
    const response = await apiClient.post('/auth/logout')
    return response.data
  },

  async changePassword(oldPassword, newPassword) {
    const response = await apiClient.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
    return response.data
  },

  async getCurrentUser() {
    const response = await apiClient.get('/auth/me')
    return response.data
  }
}
