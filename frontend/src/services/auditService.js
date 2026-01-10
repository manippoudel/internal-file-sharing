import api from './api';

class AuditService {
  async getLogs(filters = {}) {
    const response = await api.get('/audit/logs', {
      params: filters
    });
    return response.data;
  }

  async getSummary(startDate, endDate) {
    const response = await api.get('/audit/summary', {
      params: {
        start_date: startDate,
        end_date: endDate
      }
    });
    return response.data;
  }

  async exportLogs(filters = {}) {
    const response = await api.get('/audit/export', {
      params: filters,
      responseType: 'blob'
    });
    return response.data;
  }

  async getMyActivity(page = 1, perPage = 20) {
    const response = await api.get('/audit/my-activity', {
      params: {
        page,
        per_page: perPage
      }
    });
    return response.data;
  }
}

export default new AuditService();
