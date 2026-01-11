<template>
  <div class="admin-dashboard">
    <h1>Admin Dashboard</h1>
    
    <!-- Statistics Cards -->
    <div class="stats-grid" v-if="dashboardData">
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboardData.total_users }}</div>
          <div class="stat-label">Total Users</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">📁</div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboardData.total_files }}</div>
          <div class="stat-label">Total Files</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">💾</div>
        <div class="stat-info">
          <div class="stat-value">{{ formatBytes(dashboardData.total_storage_used) }}</div>
          <div class="stat-label">Storage Used</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">👤</div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboardData.active_users }}</div>
          <div class="stat-label">Active Users (24h)</div>
        </div>
      </div>
    </div>

    <!-- Storage Info -->
    <div class="storage-section" v-if="storageInfo">
      <h2>Storage Status</h2>
      <div class="storage-bar">
        <div 
          class="storage-fill" 
          :style="{ width: storageInfo.usage_percentage + '%' }"
          :class="{ warning: storageInfo.usage_percentage > 80 }"
        ></div>
      </div>
      <div class="storage-details">
        <span>{{ formatBytes(storageInfo.used_bytes) }} / {{ formatBytes(storageInfo.total_bytes) }}</span>
        <span>{{ storageInfo.usage_percentage.toFixed(1) }}% used</span>
      </div>
      <div v-if="storageInfo.usage_percentage > 80" class="storage-warning">
        ⚠️ Storage is over 80% full!
      </div>
    </div>

    <!-- System Health -->
    <div class="health-section" v-if="systemHealth">
      <h2>System Health</h2>
      <div class="health-grid">
        <div class="health-card">
          <div class="health-label">CPU Usage</div>
          <div class="health-value">{{ systemHealth.cpu_percent.toFixed(1) }}%</div>
          <div class="health-bar">
            <div 
              class="health-fill" 
              :style="{ width: systemHealth.cpu_percent + '%' }"
              :class="getHealthClass(systemHealth.cpu_percent)"
            ></div>
          </div>
        </div>
        
        <div class="health-card">
          <div class="health-label">RAM Usage</div>
          <div class="health-value">{{ systemHealth.memory_percent.toFixed(1) }}%</div>
          <div class="health-bar">
            <div 
              class="health-fill" 
              :style="{ width: systemHealth.memory_percent + '%' }"
              :class="getHealthClass(systemHealth.memory_percent)"
            ></div>
          </div>
        </div>
        
        <div class="health-card">
          <div class="health-label">Disk Usage</div>
          <div class="health-value">{{ systemHealth.disk_percent.toFixed(1) }}%</div>
          <div class="health-bar">
            <div 
              class="health-fill" 
              :style="{ width: systemHealth.disk_percent + '%' }"
              :class="getHealthClass(systemHealth.disk_percent)"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="activity-section" v-if="dashboardData">
      <h2>Recent Activity</h2>
      <div class="activity-stats">
        <div class="activity-item">
          <span>Uploads (24h):</span>
          <strong>{{ dashboardData.uploads_24h }}</strong>
        </div>
        <div class="activity-item">
          <span>Downloads (24h):</span>
          <strong>{{ dashboardData.downloads_24h }}</strong>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">Loading dashboard data...</div>
    
    <!-- Error State -->
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import adminService from '../services/adminService';

export default {
  name: 'AdminDashboard',
  setup() {
    const dashboardData = ref(null);
    const storageInfo = ref(null);
    const systemHealth = ref(null);
    const loading = ref(true);
    const error = ref(null);

    const loadDashboard = async () => {
      try {
        loading.value = true;
        error.value = null;
        
        const [dashboard, storage, health] = await Promise.all([
          adminService.getDashboard(),
          adminService.getStorageInfo(),
          adminService.getSystemHealth()
        ]);
        
        dashboardData.value = dashboard;
        storageInfo.value = storage;
        systemHealth.value = health;
      } catch (err) {
        console.error('Error loading dashboard:', err);
        error.value = err.response?.data?.detail || 'Failed to load dashboard data';
      } finally {
        loading.value = false;
      }
    };

    const formatBytes = (bytes) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    const getHealthClass = (percent) => {
      if (percent < 60) return 'good';
      if (percent < 80) return 'warning';
      return 'danger';
    };

    onMounted(() => {
      loadDashboard();
      // Refresh every 30 seconds
      const interval = setInterval(loadDashboard, 30000);
      return () => clearInterval(interval);
    });

    return {
      dashboardData,
      storageInfo,
      systemHealth,
      loading,
      error,
      formatBytes,
      getHealthClass
    };
  }
};
</script>

<style scoped>
.admin-dashboard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  color: #333;
  margin-bottom: 30px;
}

h2 {
  color: #555;
  margin: 30px 0 15px 0;
  font-size: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  font-size: 40px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #2196F3;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.storage-section,
.health-section,
.activity-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.storage-bar {
  height: 30px;
  background: #e0e0e0;
  border-radius: 15px;
  overflow: hidden;
  margin: 10px 0;
}

.storage-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #45a049);
  transition: width 0.3s;
}

.storage-fill.warning {
  background: linear-gradient(90deg, #ff9800, #f57c00);
}

.storage-details {
  display: flex;
  justify-content: space-between;
  color: #666;
  font-size: 14px;
}

.storage-warning {
  background: #fff3cd;
  color: #856404;
  padding: 10px;
  border-radius: 4px;
  margin-top: 10px;
  border: 1px solid #ffeeba;
}

.health-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.health-card {
  text-align: center;
}

.health-label {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.health-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 10px;
}

.health-bar {
  height: 10px;
  background: #e0e0e0;
  border-radius: 5px;
  overflow: hidden;
}

.health-fill {
  height: 100%;
  transition: width 0.3s;
}

.health-fill.good {
  background: #4CAF50;
}

.health-fill.warning {
  background: #ff9800;
}

.health-fill.danger {
  background: #f44336;
}

.activity-stats {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
}

.activity-item {
  display: flex;
  gap: 10px;
  align-items: center;
}

.activity-item strong {
  color: #2196F3;
  font-size: 20px;
}

.loading,
.error {
  text-align: center;
  padding: 40px;
  font-size: 16px;
}

.error {
  color: #f44336;
  background: #ffebee;
  border-radius: 4px;
}
</style>
