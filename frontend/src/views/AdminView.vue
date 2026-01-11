<template>
  <div class="admin-view-container">
    <div class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="{ active: activeTab === tab.id }"
        class="tab-button"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="tab-content">
      <AdminDashboard v-if="activeTab === 'dashboard'" />
      <UserManagement v-if="activeTab === 'users'" />
      <SchedulerManagement v-if="activeTab === 'scheduler'" />
      <AuditLogViewer v-if="activeTab === 'audit'" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import AdminDashboard from '../components/AdminDashboard.vue';
import UserManagement from '../components/UserManagement.vue';
import SchedulerManagement from '../components/SchedulerManagement.vue';
import AuditLogViewer from '../components/AuditLogViewer.vue';

const activeTab = ref('dashboard');

const tabs = [
  { id: 'dashboard', label: '📊 Dashboard' },
  { id: 'users', label: '👥 Users' },
  { id: 'scheduler', label: '⏰ Scheduler' },
  { id: 'audit', label: '📋 Audit Logs' }
];
</script>

<style scoped>
.admin-view-container {
  min-height: 100vh;
  background: #f5f5f5;
}

.tabs {
  background: white;
  border-bottom: 2px solid #e0e0e0;
  display: flex;
  padding: 0 20px;
  gap: 5px;
}

.tab-button {
  padding: 15px 25px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
}

.tab-button:hover {
  color: #2196F3;
  background: #f5f5f5;
}

.tab-button.active {
  color: #2196F3;
  border-bottom-color: #2196F3;
}

.tab-content {
  padding: 0;
}
</style>
