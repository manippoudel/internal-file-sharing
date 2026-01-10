<template>
  <div class="home-view">
    <div class="action-bar">
      <button @click="showUpload = true" class="upload-btn">
        📤 Upload Files
      </button>
    </div>
    
    <FileUpload 
      v-if="showUpload" 
      @close="showUpload = false"
      @upload-complete="handleUploadComplete"
    />
    
    <FileBrowser v-if="!showUpload" />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import FileBrowser from '../components/FileBrowser.vue';
import FileUpload from '../components/FileUpload.vue';

const showUpload = ref(false);

const handleUploadComplete = () => {
  showUpload.value = false;
};
</script>

<style scoped>
.home-view {
  padding: 20px;
}

.action-bar {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-start;
}

.upload-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 12px 24px;
  font-size: 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;
}

.upload-btn:hover {
  background-color: #45a049;
}

.upload-btn:active {
  transform: translateY(1px);
}
</style>
