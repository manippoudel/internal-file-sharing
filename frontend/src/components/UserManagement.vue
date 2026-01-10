<template>
  <div class="user-management">
    <div class="header">
      <h2>User Management</h2>
      <button @click="showCreateUser = true" class="btn-primary">+ Create User</button>
    </div>

    <!-- User Table -->
    <div class="table-container">
      <table v-if="users.length > 0">
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span class="badge" :class="user.is_admin ? 'badge-admin' : 'badge-user'">
                {{ user.is_admin ? 'Admin' : 'User' }}
              </span>
            </td>
            <td>
              <span class="badge" :class="user.is_locked ? 'badge-locked' : 'badge-active'">
                {{ user.is_locked ? 'Locked' : 'Active' }}
              </span>
            </td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>
              <div class="action-buttons">
                <button @click="editUser(user)" class="btn-small">Edit</button>
                <button v-if="user.is_locked" @click="unlockUser(user.id)" class="btn-small btn-warning">Unlock</button>
                <button @click="resetUserPassword(user.id)" class="btn-small btn-info">Reset Password</button>
                <button @click="confirmDelete(user)" class="btn-small btn-danger">Delete</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">
        <p>No users found</p>
      </div>
    </div>

    <!-- Pagination -->
    <div class="pagination" v-if="totalPages > 1">
      <button @click="currentPage--" :disabled="currentPage === 1">Previous</button>
      <span>Page {{ currentPage }} of {{ totalPages }}</span>
      <button @click="currentPage++" :disabled="currentPage === totalPages">Next</button>
    </div>

    <!-- Create/Edit User Modal -->
    <div v-if="showCreateUser || editingUser" class="modal" @click.self="closeModal">
      <div class="modal-content">
        <h3>{{ editingUser ? 'Edit User' : 'Create User' }}</h3>
        <form @submit.prevent="saveUser">
          <div class="form-group">
            <label>Username *</label>
            <input v-model="userForm.username" type="text" required :disabled="editingUser" />
          </div>
          <div class="form-group">
            <label>Email *</label>
            <input v-model="userForm.email" type="email" required />
          </div>
          <div class="form-group" v-if="!editingUser">
            <label>Password *</label>
            <input v-model="userForm.password" type="password" required minlength="12" />
            <small>Minimum 12 characters with uppercase, lowercase, digit, and special character</small>
          </div>
          <div class="form-group">
            <label>
              <input v-model="userForm.is_admin" type="checkbox" />
              Administrator
            </label>
          </div>
          <div class="form-actions">
            <button type="button" @click="closeModal" class="btn-secondary">Cancel</button>
            <button type="submit" class="btn-primary">{{ editingUser ? 'Update' : 'Create' }}</button>
          </div>
        </form>
        <div v-if="formError" class="error">{{ formError }}</div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="deleteConfirm" class="modal" @click.self="deleteConfirm = null">
      <div class="modal-content">
        <h3>Confirm Delete</h3>
        <p>Are you sure you want to delete user <strong>{{ deleteConfirm.username }}</strong>?</p>
        <div class="form-actions">
          <button @click="deleteConfirm = null" class="btn-secondary">Cancel</button>
          <button @click="deleteUser(deleteConfirm.id)" class="btn-danger">Delete</button>
        </div>
      </div>
    </div>

    <!-- Loading/Error States -->
    <div v-if="loading" class="loading">Loading users...</div>
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue';
import adminService from '../services/adminService';

export default {
  name: 'UserManagement',
  setup() {
    const users = ref([]);
    const currentPage = ref(1);
    const totalPages = ref(1);
    const loading = ref(false);
    const error = ref(null);
    const formError = ref(null);
    
    const showCreateUser = ref(false);
    const editingUser = ref(null);
    const deleteConfirm = ref(null);
    
    const userForm = ref({
      username: '',
      email: '',
      password: '',
      is_admin: false
    });

    const loadUsers = async () => {
      try {
        loading.value = true;
        error.value = null;
        const response = await adminService.getUsers(currentPage.value, 20);
        users.value = response.users || response;
        totalPages.value = response.total_pages || 1;
      } catch (err) {
        console.error('Error loading users:', err);
        error.value = err.response?.data?.detail || 'Failed to load users';
      } finally {
        loading.value = false;
      }
    };

    const saveUser = async () => {
      try {
        formError.value = null;
        if (editingUser.value) {
          await adminService.updateUser(editingUser.value.id, {
            email: userForm.value.email,
            is_admin: userForm.value.is_admin
          });
        } else {
          await adminService.createUser(userForm.value);
        }
        closeModal();
        await loadUsers();
      } catch (err) {
        console.error('Error saving user:', err);
        formError.value = err.response?.data?.detail || 'Failed to save user';
      }
    };

    const editUser = (user) => {
      editingUser.value = user;
      userForm.value = {
        username: user.username,
        email: user.email,
        is_admin: user.is_admin
      };
    };

    const unlockUser = async (userId) => {
      try {
        await adminService.unlockUser(userId);
        await loadUsers();
      } catch (err) {
        console.error('Error unlocking user:', err);
        error.value = err.response?.data?.detail || 'Failed to unlock user';
      }
    };

    const resetUserPassword = async (userId) => {
      try {
        const result = await adminService.resetPassword(userId);
        alert(`Password reset! New password: ${result.new_password}\n\nPlease save this password securely.`);
      } catch (err) {
        console.error('Error resetting password:', err);
        error.value = err.response?.data?.detail || 'Failed to reset password';
      }
    };

    const confirmDelete = (user) => {
      deleteConfirm.value = user;
    };

    const deleteUser = async (userId) => {
      try {
        await adminService.deleteUser(userId);
        deleteConfirm.value = null;
        await loadUsers();
      } catch (err) {
        console.error('Error deleting user:', err);
        error.value = err.response?.data?.detail || 'Failed to delete user';
      }
    };

    const closeModal = () => {
      showCreateUser.value = false;
      editingUser.value = null;
      formError.value = null;
      userForm.value = {
        username: '',
        email: '',
        password: '',
        is_admin: false
      };
    };

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString();
    };

    watch(currentPage, () => {
      loadUsers();
    });

    onMounted(() => {
      loadUsers();
    });

    return {
      users,
      currentPage,
      totalPages,
      loading,
      error,
      formError,
      showCreateUser,
      editingUser,
      deleteConfirm,
      userForm,
      saveUser,
      editUser,
      unlockUser,
      resetUserPassword,
      confirmDelete,
      deleteUser,
      closeModal,
      formatDate
    };
  }
};
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
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

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.badge-admin {
  background: #e3f2fd;
  color: #1976d2;
}

.badge-user {
  background: #f3e5f5;
  color: #7b1fa2;
}

.badge-active {
  background: #e8f5e9;
  color: #2e7d32;
}

.badge-locked {
  background: #ffebee;
  color: #c62828;
}

.action-buttons {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.btn-primary, .btn-secondary, .btn-small, .btn-danger, .btn-warning, .btn-info {
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

.btn-primary:hover {
  background: #1976D2;
}

.btn-secondary {
  background: #757575;
  color: white;
}

.btn-secondary:hover {
  background: #616161;
}

.btn-small {
  padding: 4px 8px;
  font-size: 12px;
  background: #e0e0e0;
}

.btn-small:hover {
  background: #bdbdbd;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.btn-danger:hover {
  background: #d32f2f;
}

.btn-warning {
  background: #ff9800;
  color: white;
}

.btn-info {
  background: #03a9f4;
  color: white;
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
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin-top: 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.form-group input[type="text"],
.form-group input[type="email"],
.form-group input[type="password"] {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group small {
  display: block;
  margin-top: 5px;
  color: #666;
  font-size: 12px;
}

.form-actions {
  display: flex;
  gap: 10px;
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
