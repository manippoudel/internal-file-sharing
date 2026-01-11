import api from './api';

class AdminService {
  // User Management
  async getUsers(page = 1, perPage = 20) {
    const response = await api.get('/admin/users', {
      params: { page, per_page: perPage }
    });
    return response.data;
  }

  async getUser(userId) {
    const response = await api.get(`/admin/users/${userId}`);
    return response.data;
  }

  async createUser(userData) {
    const response = await api.post('/admin/users', userData);
    return response.data;
  }

  async updateUser(userId, userData) {
    const response = await api.put(`/admin/users/${userId}`, userData);
    return response.data;
  }

  async deleteUser(userId) {
    const response = await api.delete(`/admin/users/${userId}`);
    return response.data;
  }

  async unlockUser(userId) {
    const response = await api.post(`/admin/users/${userId}/unlock`);
    return response.data;
  }

  async resetPassword(userId) {
    const response = await api.post(`/admin/users/${userId}/reset-password`);
    return response.data;
  }

  // Dashboard & Statistics
  async getDashboard() {
    const response = await api.get('/admin/dashboard');
    return response.data;
  }

  async getStorageInfo() {
    const response = await api.get('/admin/storage');
    return response.data;
  }

  async getSystemHealth() {
    const response = await api.get('/admin/system-health');
    return response.data;
  }

  async getSettings() {
    const response = await api.get('/admin/settings');
    return response.data;
  }
}

export default new AdminService();
