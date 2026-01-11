import { defineStore } from 'pinia'
import fileService from '../services/fileService'

export const useFileStore = defineStore('files', {
  state: () => ({
    files: [],
    total: 0,
    page: 1,
    pageSize: 100,
    totalPages: 0,
    loading: false,
    error: null,
    sortBy: 'upload_date',
    sortOrder: 'desc',
    searchQuery: '',
    selectedFiles: []
  }),

  actions: {
    async fetchFiles(includeDeleted = false) {
      this.loading = true
      this.error = null
      
      try {
        const response = await fileService.listFiles(
          this.page,
          this.pageSize,
          this.sortBy,
          this.sortOrder,
          this.searchQuery || null,
          includeDeleted
        )
        
        this.files = response.items
        this.total = response.total
        this.totalPages = response.total_pages
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch files'
        console.error('Fetch files error:', error)
      } finally {
        this.loading = false
      }
    },

    async deleteFile(fileId) {
      try {
        await fileService.deleteFile(fileId)
        await this.fetchFiles()
        return true
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to delete file'
        return false
      }
    },

    async restoreFile(fileId) {
      try {
        await fileService.restoreFile(fileId)
        await this.fetchFiles(true)
        return true
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to restore file'
        return false
      }
    },

    async renameFile(fileId, newFilename) {
      try {
        await fileService.renameFile(fileId, newFilename)
        await this.fetchFiles()
        return true
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to rename file'
        return false
      }
    },

    async downloadFile(file) {
      try {
        await fileService.downloadFile(file.id, file.filename)
        return true
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to download file'
        return false
      }
    },

    async bulkDownload() {
      if (this.selectedFiles.length === 0) return false
      
      try {
        await fileService.bulkDownload(this.selectedFiles)
        return true
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to download files'
        return false
      }
    },

    setPage(page) {
      this.page = page
      this.fetchFiles()
    },

    setSort(sortBy, sortOrder) {
      this.sortBy = sortBy
      this.sortOrder = sortOrder
      this.fetchFiles()
    },

    setSearch(query) {
      this.searchQuery = query
      this.page = 1
      this.fetchFiles()
    },

    toggleFileSelection(fileId) {
      const index = this.selectedFiles.indexOf(fileId)
      if (index > -1) {
        this.selectedFiles.splice(index, 1)
      } else {
        this.selectedFiles.push(fileId)
      }
    },

    selectAll() {
      this.selectedFiles = this.files.map(f => f.id)
    },

    clearSelection() {
      this.selectedFiles = []
    }
  }
})
