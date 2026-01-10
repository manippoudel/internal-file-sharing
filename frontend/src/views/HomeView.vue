<template>
  <div class="home">
    <h1>Internal File Sharing System</h1>
    <p>Welcome to the Internal File Sharing System</p>
    <p>Status: {{ status }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const status = ref('Loading...')

onMounted(async () => {
  try {
    const response = await fetch('/api/v1/')
    const data = await response.json()
    status.value = data.status || 'running'
  } catch (error) {
    status.value = 'Error connecting to server'
    console.error('Error:', error)
  }
})
</script>

<style scoped>
.home {
  padding: 2rem;
  text-align: center;
}

h1 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

p {
  margin-bottom: 0.5rem;
  color: #666;
}
</style>
