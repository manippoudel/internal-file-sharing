<template>
  <div id="app">
    <nav v-if="authStore.isAuthenticated" class="navbar">
      <div class="nav-brand">
        <h1>Internal File Sharing</h1>
      </div>
      <div class="nav-menu">
        <router-link to="/">Files</router-link>
        <router-link v-if="authStore.isAdmin" to="/admin">Admin</router-link>
        <div class="user-menu">
          <span>{{ authStore.user?.username }}</span>
          <button @click="handleLogout" class="btn-logout">Logout</button>
        </div>
      </div>
    </nav>
    
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const router = useRouter()

onMounted(async () => {
  if (authStore.isAuthenticated) {
    await authStore.fetchCurrentUser()
  }
})

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f3f4f6;
}

#app {
  width: 100%;
  min-height: 100vh;
}

.navbar {
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand h1 {
  font-size: 1.5rem;
  color: #667eea;
}

.nav-menu {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.nav-menu a {
  text-decoration: none;
  color: #333;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 4px;
}

.nav-menu a:hover {
  background: #f3f4f6;
}

.nav-menu a.router-link-active {
  background: #667eea;
  color: white;
}

.user-menu {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.btn-logout {
  padding: 0.5rem 1rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-logout:hover {
  background: #dc2626;
}
</style>
