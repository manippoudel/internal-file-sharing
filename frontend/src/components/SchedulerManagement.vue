<template>
  <div class="scheduler-management">
    <h1>Scheduler Management</h1>
    
    <div class="scheduler-status" v-if="schedulerStatus">
      <div class="status-card">
        <span class="status-label">Scheduler Status:</span>
        <span class="status-value" :class="schedulerStatus.running ? 'running' : 'stopped'">
          {{ schedulerStatus.running ? '🟢 Running' : '🔴 Stopped' }}
        </span>
      </div>
    </div>

    <!-- Tasks Table -->
    <div class="table-container">
      <table v-if="tasks.length > 0">
        <thead>
          <tr>
            <th>Task Name</th>
            <th>Schedule</th>
            <th>Status</th>
            <th>Last Run</th>
            <th>Next Run</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task.id">
            <td>
              <div class="task-name">{{ task.name }}</div>
              <div class="task-description">{{ task.description }}</div>
            </td>
            <td><code>{{ task.schedule }}</code></td>
            <td>
              <span class="badge" :class="task.is_active ? 'badge-active' : 'badge-paused'">
                {{ task.is_active ? 'Active' : 'Paused' }}
              </span>
            </td>
            <td>{{ formatDate(task.last_run_at) }}</td>
            <td>{{ formatDate(task.next_run_at) }}</td>
            <td>
              <div class="action-buttons">
                <button 
                  v-if="task.is_active" 
                  @click="pauseTask(task.id)" 
                  class="btn-small btn-warning"
                >
                  Pause
                </button>
                <button 
                  v-else 
                  @click="resumeTask(task.id)" 
                  class="btn-small btn-success"
                >
                  Resume
                </button>
                <button @click="triggerTask(task.id)" class="btn-small btn-primary">
                  Trigger Now
                </button>
                <button @click="viewDetails(task)" class="btn-small">
                  Details
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">
        <p>No scheduled tasks found</p>
      </div>
    </div>

    <!-- Task Details Modal -->
    <div v-if="selectedTask" class="modal" @click.self="selectedTask = null">
      <div class="modal-content">
        <h3>{{ selectedTask.name }}</h3>
        <div class="detail-group">
          <label>Description:</label>
          <p>{{ selectedTask.description }}</p>
        </div>
        <div class="detail-group">
          <label>Schedule:</label>
          <p><code>{{ selectedTask.schedule }}</code></p>
        </div>
        <div class="detail-group">
          <label>Status:</label>
          <p>{{ selectedTask.is_active ? 'Active' : 'Paused' }}</p>
        </div>
        <div class="detail-group">
          <label>Last Run:</label>
          <p>{{ formatDate(selectedTask.last_run_at) }}</p>
        </div>
        <div class="detail-group">
          <label>Next Run:</label>
          <p>{{ formatDate(selectedTask.next_run_at) }}</p>
        </div>
        <div class="detail-group">
          <label>Last Result:</label>
          <p>{{ selectedTask.last_result || 'N/A' }}</p>
        </div>
        <div class="form-actions">
          <button @click="selectedTask = null" class="btn-secondary">Close</button>
        </div>
      </div>
    </div>

    <!-- Loading/Error States -->
    <div v-if="loading" class="loading">Loading tasks...</div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="successMessage" class="success">{{ successMessage }}</div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import schedulerService from '../services/schedulerService';

export default {
  name: 'SchedulerManagement',
  setup() {
    const tasks = ref([]);
    const schedulerStatus = ref(null);
    const selectedTask = ref(null);
    const loading = ref(false);
    const error = ref(null);
    const successMessage = ref(null);

    const loadData = async () => {
      try {
        loading.value = true;
        error.value = null;
        
        const [tasksData, statusData] = await Promise.all([
          schedulerService.getTasks(),
          schedulerService.getStatus()
        ]);
        
        tasks.value = tasksData.tasks || tasksData;
        schedulerStatus.value = statusData;
      } catch (err) {
        console.error('Error loading scheduler data:', err);
        error.value = err.response?.data?.detail || 'Failed to load scheduler data';
      } finally {
        loading.value = false;
      }
    };

    const pauseTask = async (taskId) => {
      try {
        error.value = null;
        successMessage.value = null;
        await schedulerService.pauseTask(taskId);
        successMessage.value = 'Task paused successfully';
        await loadData();
        setTimeout(() => successMessage.value = null, 3000);
      } catch (err) {
        console.error('Error pausing task:', err);
        error.value = err.response?.data?.detail || 'Failed to pause task';
      }
    };

    const resumeTask = async (taskId) => {
      try {
        error.value = null;
        successMessage.value = null;
        await schedulerService.resumeTask(taskId);
        successMessage.value = 'Task resumed successfully';
        await loadData();
        setTimeout(() => successMessage.value = null, 3000);
      } catch (err) {
        console.error('Error resuming task:', err);
        error.value = err.response?.data?.detail || 'Failed to resume task';
      }
    };

    const triggerTask = async (taskId) => {
      if (!confirm('Are you sure you want to trigger this task now?')) {
        return;
      }
      
      try {
        error.value = null;
        successMessage.value = null;
        await schedulerService.triggerTask(taskId);
        successMessage.value = 'Task triggered successfully';
        setTimeout(() => successMessage.value = null, 3000);
      } catch (err) {
        console.error('Error triggering task:', err);
        error.value = err.response?.data?.detail || 'Failed to trigger task';
      }
    };

    const viewDetails = (task) => {
      selectedTask.value = task;
    };

    const formatDate = (dateString) => {
      if (!dateString) return 'Never';
      return new Date(dateString).toLocaleString();
    };

    onMounted(() => {
      loadData();
      // Refresh every 30 seconds
      const interval = setInterval(loadData, 30000);
      return () => clearInterval(interval);
    });

    return {
      tasks,
      schedulerStatus,
      selectedTask,
      loading,
      error,
      successMessage,
      pauseTask,
      resumeTask,
      triggerTask,
      viewDetails,
      formatDate
    };
  }
};
</script>

<style scoped>
.scheduler-management {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  color: #333;
  margin-bottom: 20px;
}

.scheduler-status {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.status-card {
  display: flex;
  align-items: center;
  gap: 15px;
}

.status-label {
  font-weight: 600;
  color: #666;
}

.status-value {
  font-size: 18px;
  font-weight: 500;
}

.status-value.running {
  color: #4CAF50;
}

.status-value.stopped {
  color: #f44336;
}

.table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

th {
  background: #f5f5f5;
  font-weight: 600;
  color: #333;
}

.task-name {
  font-weight: 500;
  color: #333;
}

.task-description {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.badge-active {
  background: #e8f5e9;
  color: #2e7d32;
}

.badge-paused {
  background: #fff3e0;
  color: #e65100;
}

.action-buttons {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.btn-small, .btn-primary, .btn-secondary, .btn-warning, .btn-success {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-small {
  background: #e0e0e0;
  color: #333;
}

.btn-small:hover {
  background: #bdbdbd;
}

.btn-primary {
  background: #2196F3;
  color: white;
}

.btn-secondary {
  background: #757575;
  color: white;
}

.btn-warning {
  background: #ff9800;
  color: white;
}

.btn-success {
  background: #4CAF50;
  color: white;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 20px;
}

.detail-group {
  margin-bottom: 15px;
}

.detail-group label {
  display: block;
  font-weight: 600;
  color: #666;
  margin-bottom: 5px;
}

.detail-group p {
  margin: 0;
  color: #333;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.loading, .error, .success {
  padding: 15px;
  border-radius: 4px;
  margin-top: 15px;
  text-align: center;
}

.error {
  background: #ffebee;
  color: #c62828;
}

.success {
  background: #e8f5e9;
  color: #2e7d32;
}
</style>
