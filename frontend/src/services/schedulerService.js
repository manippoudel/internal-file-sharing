import api from './api';

class SchedulerService {
  async getTasks() {
    const response = await api.get('/scheduler/tasks');
    return response.data;
  }

  async getTask(taskId) {
    const response = await api.get(`/scheduler/tasks/${taskId}`);
    return response.data;
  }

  async pauseTask(taskId) {
    const response = await api.post(`/scheduler/tasks/${taskId}/pause`);
    return response.data;
  }

  async resumeTask(taskId) {
    const response = await api.post(`/scheduler/tasks/${taskId}/resume`);
    return response.data;
  }

  async triggerTask(taskId) {
    const response = await api.post(`/scheduler/tasks/${taskId}/trigger`);
    return response.data;
  }

  async getStatus() {
    const response = await api.get('/scheduler/status');
    return response.data;
  }
}

export default new SchedulerService();
