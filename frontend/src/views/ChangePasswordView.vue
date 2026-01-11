<template>
  <div class="change-password-container">
    <div class="change-password-card">
      <h2>Change Password</h2>
      <p v-if="mustChange" class="warning">
        You must change your password before continuing.
      </p>
      
      <form @submit.prevent="handleChangePassword">
        <div class="form-group">
          <label for="old-password">Current Password</label>
          <input
            id="old-password"
            v-model="oldPassword"
            type="password"
            required
            :disabled="loading"
          />
        </div>
        
        <div class="form-group">
          <label for="new-password">New Password</label>
          <input
            id="new-password"
            v-model="newPassword"
            type="password"
            required
            :disabled="loading"
          />
          <small>Minimum 12 characters with uppercase, lowercase, digit, and special character</small>
        </div>
        
        <div class="form-group">
          <label for="confirm-password">Confirm New Password</label>
          <input
            id="confirm-password"
            v-model="confirmPassword"
            type="password"
            required
            :disabled="loading"
          />
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <div v-if="success" class="success-message">
          Password changed successfully!
        </div>
        
        <button type="submit" :disabled="loading" class="btn-primary">
          {{ loading ? 'Changing...' : 'Change Password' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const error = ref(null)
const success = ref(false)
const loading = ref(false)

const mustChange = computed(() => authStore.mustChangePassword)

const handleChangePassword = async () => {
  error.value = null
  success.value = false
  
  if (newPassword.value !== confirmPassword.value) {
    error.value = 'New passwords do not match'
    return
  }
  
  if (newPassword.value.length < 12) {
    error.value = 'Password must be at least 12 characters long'
    return
  }
  
  loading.value = true
  
  const result = await authStore.changePassword(oldPassword.value, newPassword.value)
  
  if (result) {
    success.value = true
    setTimeout(() => {
      router.push('/')
    }, 1500)
  } else {
    error.value = authStore.error || 'Password change failed'
  }
  
  loading.value = false
}
</script>

<style scoped>
.change-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 80px);
  padding: 2rem;
}

.change-password-card {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 500px;
}

h2 {
  margin-bottom: 1rem;
  color: #333;
}

.warning {
  background-color: #fef3c7;
  border: 1px solid #f59e0b;
  color: #92400e;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #555;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

small {
  display: block;
  margin-top: 0.25rem;
  color: #6b7280;
  font-size: 0.875rem;
}

.error-message {
  background-color: #fee;
  border: 1px solid #fcc;
  color: #c33;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.success-message {
  background-color: #efe;
  border: 1px solid #cfc;
  color: #3c3;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.btn-primary {
  width: 100%;
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary:hover:not(:disabled) {
  background: #5568d3;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
