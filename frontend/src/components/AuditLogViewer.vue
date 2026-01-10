<template>
  <div class="audit-log-viewer">
    <h1>Audit Logs</h1>

    <!-- Filters -->
    <div class="filters">
      <div class="filter-group">
        <label>User:</label>
        <input v-model="filters.user" type="text" placeholder="Filter by username" />
      </div>
      <div class="filter-group">
        <label>Action:</label>
        <select v-model="filters.action">
          <option value="">All Actions</option>
          <option value="login">Login</option>
          <option value="logout">Logout</option>
          <option value="file_upload">File Upload</option>
          <option value="file_download">File Download</option>
          <option value="file_delete">File Delete</option>
          <option value="file_restore">File Restore</option>
          <option value="user_create">User Create</option>
          <option value="user_update">User Update</option>
          <option value="user_delete">User Delete</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Start Date:</label>
        <input v-model="filters.startDate" type="date" />
      </div>
      <div class="filter-group">
        <label>End Date:</label>
        <input v-model="filters.endDate" type="date" />
      </div>
      <div class="filter-actions">
        <button @click="applyFilters" class="btn-primary">Apply Filters</button>
        <button @click="resetFilters" class="btn-secondary">Reset</button>
        <button @click="exportLogs" class="btn-export">📥 Export CSV</button>
      </div>
    </div>

    <!-- Logs Table -->
    <div class="table-container">
      <table v-if="logs.length > 0">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>User</th>
            <th>Action</th>
            <th>Resource</th>
            <th>IP Address</th>
            <th>User Agent</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id">
            <td>{{ formatDate(log.timestamp) }}</td>
            <td>{{ log.username }}</td>
            <td>
              <span class="badge" :class="getActionClass(log.action)">
                {{ formatAction(log.action) }}
              </span>
            </td>
            <td>{{ log.resource_type || '-' }}</td>
            <td><code>{{ log.ip_address }}</code></td>
            <td class="user-agent">{{ log.user_agent }}</td>
            <td>
              <button @click="viewDetails(log)" class="btn-small">View</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">
        <p>No audit logs found</p>
      </div>
    </div>

    <!-- Pagination -->
    <div class="pagination" v-if="totalPages > 1">
      <button @click="currentPage--" :disabled="currentPage === 1">Previous</button>
      <span>Page {{ currentPage }} of {{ totalPages }}</span>
      <button @click="currentPage++" :disabled="currentPage === totalPages">Next</button>
    </div>

    <!-- Log Details Modal -->
    <div v-if="selectedLog" class="modal" @click.self="selectedLog = null">
      <div class="modal-content">
        <h3>Audit Log Details</h3>
        <div class="detail-group">
          <label>Timestamp:</label>
          <p>{{ formatDate(selectedLog.timestamp) }}</p>
        </div>
        <div class="detail-group">
          <label>User:</label>
          <p>{{ selectedLog.username }}</p>
        </div>
        <div class="detail-group">
          <label>Action:</label>
          <p>{{ formatAction(selectedLog.action) }}</p>
        </div>
        <div class="detail-group">
          <label>Resource Type:</label>
          <p>{{ selectedLog.resource_type || 'N/A' }}</p>
        </div>
        <div class="detail-group">
          <label>Resource ID:</label>
          <p>{{ selectedLog.resource_id || 'N/A' }}</p>
        </div>
        <div class="detail-group">
          <label>IP Address:</label>
          <p><code>{{ selectedLog.ip_address }}</code></p>
        </div>
        <div class="detail-group">
          <label>User Agent:</label>
          <p>{{ selectedLog.user_agent }}</p>
        </div>
        <div class="detail-group" v-if="selectedLog.details">
          <label>Additional Details:</label>
          <pre>{{ JSON.stringify(selectedLog.details, null, 2) }}</pre>
        </div>
        <div class="form-actions">
          <button @click="selectedLog = null" class="btn-secondary">Close</button>
        </div>
      </div>
    </div>

    <!-- Loading/Error States -->
    <div v-if="loading" class="loading">Loading audit logs...</div>
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue';
import auditService from '../services/auditService';

export default {
  name: 'AuditLogViewer',
  setup() {
    const logs = ref([]);
    const currentPage = ref(1);
    const totalPages = ref(1);
    const loading = ref(false);
    const error = ref(null);
    const selectedLog = ref(null);
    
    const filters = ref({
      user: '',
      action: '',
      startDate: '',
      endDate: ''
    });

    const loadLogs = async () => {
      try {
        loading.value = true;
        error.value = null;
        
        const params = {
          page: currentPage.value,
          per_page: 50
        };
        
        if (filters.value.user) params.username = filters.value.user;
        if (filters.value.action) params.action = filters.value.action;
        if (filters.value.startDate) params.start_date = filters.value.startDate;
        if (filters.value.endDate) params.end_date = filters.value.endDate;
        
        const response = await auditService.getLogs(params);
        logs.value = response.logs || response;
        totalPages.value = response.total_pages || 1;
      } catch (err) {
        console.error('Error loading audit logs:', err);
        error.value = err.response?.data?.detail || 'Failed to load audit logs';
      } finally {
        loading.value = false;
      }
    };

    const applyFilters = () => {
      currentPage.value = 1;
      loadLogs();
    };

    const resetFilters = () => {
      filters.value = {
        user: '',
        action: '',
        startDate: '',
        endDate: ''
      };
      currentPage.value = 1;
      loadLogs();
    };

    const exportLogs = async () => {
      try {
        const params = {};
        if (filters.value.user) params.username = filters.value.user;
        if (filters.value.action) params.action = filters.value.action;
        if (filters.value.startDate) params.start_date = filters.value.startDate;
        if (filters.value.endDate) params.end_date = filters.value.endDate;
        
        const blob = await auditService.exportLogs(params);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit_logs_${new Date().toISOString()}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } catch (err) {
        console.error('Error exporting logs:', err);
        error.value = err.response?.data?.detail || 'Failed to export logs';
      }
    };

    const viewDetails = (log) => {
      selectedLog.value = log;
    };

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString();
    };

    const formatAction = (action) => {
      return action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    const getActionClass = (action) => {
      if (action.includes('login')) return 'action-login';
      if (action.includes('logout')) return 'action-logout';
      if (action.includes('create') || action.includes('upload')) return 'action-create';
      if (action.includes('delete')) return 'action-delete';
      if (action.includes('update') || action.includes('restore')) return 'action-update';
      return 'action-default';
    };

    watch(currentPage, () => {
      loadLogs();
    });

    onMounted(() => {
      loadLogs();
    });

    return {
      logs,
      currentPage,
      totalPages,
      loading,
      error,
      selectedLog,
      filters,
      applyFilters,
      resetFilters,
      exportLogs,
      viewDetails,
      formatDate,
      formatAction,
      getActionClass
    };
  }
};
</script>

<style scoped>
.audit-log-viewer {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

h1 {
  color: #333;
  margin-bottom: 20px;
}

.filters {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: flex-end;
}

.filter-group {
  flex: 1;
  min-width: 150px;
}

.filter-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #666;
  font-size: 14px;
}

.filter-group input,
.filter-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.filter-actions {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.btn-primary, .btn-secondary, .btn-export, .btn-small {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary {
  background: #2196F3;
  color: white;
}

.btn-secondary {
  background: #757575;
  color: white;
}

.btn-export {
  background: #4CAF50;
  color: white;
}

.btn-small {
  padding: 4px 8px;
  font-size: 12px;
  background: #e0e0e0;
  color: #333;
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
  font-size: 14px;
}

td {
  font-size: 13px;
}

.user-agent {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  color: #666;
}

code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
}

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.action-login {
  background: #e3f2fd;
  color: #1976d2;
}

.action-logout {
  background: #fff3e0;
  color: #e65100;
}

.action-create {
  background: #e8f5e9;
  color: #2e7d32;
}

.action-delete {
  background: #ffebee;
  color: #c62828;
}

.action-update {
  background: #f3e5f5;
  color: #7b1fa2;
}

.action-default {
  background: #f5f5f5;
  color: #666;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  max-width: 700px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
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
  font-size: 14px;
}

.detail-group p {
  margin: 0;
  color: #333;
}

.detail-group pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
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

.loading, .error {
  padding: 20px;
  text-align: center;
}

.error {
  color: #f44336;
  background: #ffebee;
  border-radius: 4px;
  margin-top: 10px;
}
</style>
