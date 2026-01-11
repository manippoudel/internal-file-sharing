<template>
  <div class="file-browser">
    <div class="header">
      <h2>Files</h2>
      <div class="actions">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search files..."
          class="search-input"
          @input="handleSearch"
        />
        <button @click="showUploadDialog = true" class="btn-primary">
          Upload File
        </button>
        <button
          v-if="selectedFiles.length > 0"
          @click="handleBulkDownload"
          class="btn-secondary"
        >
          Download Selected ({{ selectedFiles.length }})
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading files...</div>
    
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else class="file-list">
      <table>
        <thead>
          <tr>
            <th>
              <input
                type="checkbox"
                @change="toggleSelectAll"
                :checked="allSelected"
              />
            </th>
            <th @click="sortBy('filename')" class="sortable">
              Filename {{ getSortIcon('filename') }}
            </th>
            <th @click="sortBy('size')" class="sortable">
              Size {{ getSortIcon('size') }}
            </th>
            <th>Uploaded By</th>
            <th @click="sortBy('upload_date')" class="sortable">
              Upload Date {{ getSortIcon('upload_date') }}
            </th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="file in files" :key="file.id">
            <td>
              <input
                type="checkbox"
                :checked="isSelected(file.id)"
                @change="toggleSelection(file.id)"
              />
            </td>
            <td>{{ file.filename }}</td>
            <td>{{ formatSize(file.size) }}</td>
            <td>{{ file.uploader_username }}</td>
            <td>{{ formatDate(file.upload_date) }}</td>
            <td>
              <button @click="downloadFile(file)" class="btn-icon" title="Download">
                ⬇️
              </button>
              <button @click="renameFile(file)" class="btn-icon" title="Rename">
                ✏️
              </button>
              <button @click="deleteFile(file)" class="btn-icon" title="Delete">
                🗑️
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div v-if="files.length === 0" class="empty-state">
        No files found
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button
          @click="goToPage(page - 1)"
          :disabled="page === 1"
          class="btn-secondary"
        >
          Previous
        </button>
        <span>Page {{ page }} of {{ totalPages }}</span>
        <button
          @click="goToPage(page + 1)"
          :disabled="page === totalPages"
          class="btn-secondary"
        >
          Next
        </button>
      </div>
    </div>

    <!-- Upload Dialog - Placeholder -->
    <div v-if="showUploadDialog" class="modal">
      <div class="modal-content">
        <h3>Upload File</h3>
        <p>Upload functionality will use Uppy.js (to be implemented)</p>
        <button @click="showUploadDialog = false" class="btn-primary">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useFileStore } from '../stores/files'

const fileStore = useFileStore()

const searchQuery = ref('')
const showUploadDialog = ref(false)

const files = computed(() => fileStore.files)
const loading = computed(() => fileStore.loading)
const error = computed(() => fileStore.error)
const page = computed(() => fileStore.page)
const totalPages = computed(() => fileStore.totalPages)
const selectedFiles = computed(() => fileStore.selectedFiles)
const currentSort = computed(() => fileStore.sortBy)
const currentSortOrder = computed(() => fileStore.sortOrder)

const allSelected = computed(() => {
  return files.value.length > 0 && selectedFiles.value.length === files.value.length
})

onMounted(() => {
  fileStore.fetchFiles()
})

const handleSearch = () => {
  fileStore.setSearch(searchQuery.value)
}

const sortBy = (field) => {
  const newOrder = currentSort.value === field && currentSortOrder.value === 'asc' ? 'desc' : 'asc'
  fileStore.setSort(field, newOrder)
}

const getSortIcon = (field) => {
  if (currentSort.value !== field) return ''
  return currentSortOrder.value === 'asc' ? '▲' : '▼'
}

const isSelected = (fileId) => {
  return selectedFiles.value.includes(fileId)
}

const toggleSelection = (fileId) => {
  fileStore.toggleFileSelection(fileId)
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    fileStore.clearSelection()
  } else {
    fileStore.selectAll()
  }
}

const downloadFile = async (file) => {
  await fileStore.downloadFile(file)
}

const handleBulkDownload = async () => {
  await fileStore.bulkDownload()
}

const renameFile = async (file) => {
  const newName = prompt('Enter new filename:', file.filename)
  if (newName && newName !== file.filename) {
    await fileStore.renameFile(file.id, newName)
  }
}

const deleteFile = async (file) => {
  if (confirm(`Are you sure you want to delete "${file.filename}"?`)) {
    await fileStore.deleteFile(file.id)
  }
}

const goToPage = (newPage) => {
  fileStore.setPage(newPage)
}

const formatSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString()
}
</script>

<style scoped>
.file-browser {
  padding: 2rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.actions {
  display: flex;
  gap: 1rem;
}

.search-input {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  min-width: 250px;
}

.btn-primary, .btn-secondary, .btn-icon {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5568d3;
}

.btn-secondary {
  background: #f3f4f6;
  color: #333;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  background: none;
  padding: 0.25rem 0.5rem;
  font-size: 1.2rem;
}

.btn-icon:hover {
  background: #f3f4f6;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

th, td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

th {
  background: #f9fafb;
  font-weight: 600;
}

.sortable {
  cursor: pointer;
  user-select: none;
}

.sortable:hover {
  background: #f3f4f6;
}

.loading, .error, .empty-state {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
}

.error {
  color: #dc2626;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  min-width: 400px;
}
</style>
