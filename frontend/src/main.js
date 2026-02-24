import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(router)

// Initialize auth store and fetch user if token exists
const authStore = useAuthStore()

// Wait for user data to load before mounting app
async function initApp() {
  if (authStore.token) {
    try {
      await authStore.fetchCurrentUser()
    } catch (error) {
      console.error('Failed to fetch current user:', error)
    }
  }
  app.mount('#app')
}

initApp()
