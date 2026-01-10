import apiClient from './api'

export default {
  async initUpload(filename, fileSize, totalChunks, mimeType = null) {
    const response = await apiClient.post('/files/upload/init', {
      filename,
      file_size: fileSize,
      total_chunks: totalChunks,
      mime_type: mimeType
    })
    return response.data
  },

  async uploadChunk(uploadId, chunkNumber, chunkFile, checksum, filename, totalChunks) {
    const formData = new FormData()
    formData.append('chunk_file', chunkFile)
    
    const response = await apiClient.post('/files/upload/chunk', formData, {
      params: {
        upload_id: uploadId,
        chunk_number: chunkNumber,
        checksum,
        filename,
        total_chunks: totalChunks
      },
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  async completeUpload(uploadId, finalChecksum) {
    const response = await apiClient.post('/files/upload/complete', {
      upload_id: uploadId,
      final_checksum: finalChecksum
    })
    return response.data
  },

  async cancelUpload(uploadId) {
    const response = await apiClient.post('/files/upload/cancel', null, {
      params: { upload_id: uploadId }
    })
    return response.data
  },

  async listFiles(page = 1, pageSize = 100, sortBy = 'upload_date', sortOrder = 'desc', search = null, includeDeleted = false) {
    const response = await apiClient.get('/files', {
      params: {
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
        search,
        include_deleted: includeDeleted
      }
    })
    return response.data
  },

  async getFile(fileId) {
    const response = await apiClient.get(`/files/${fileId}`)
    return response.data
  },

  async downloadFile(fileId, filename) {
    const response = await apiClient.get(`/files/${fileId}/download`, {
      responseType: 'blob'
    })
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  async bulkDownload(fileIds) {
    const response = await apiClient.post('/files/download/bulk', {
      file_ids: fileIds
    }, {
      responseType: 'blob'
    })
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'files.zip')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  async deleteFile(fileId) {
    const response = await apiClient.delete(`/files/${fileId}`)
    return response.data
  },

  async restoreFile(fileId) {
    const response = await apiClient.post(`/files/${fileId}/restore`)
    return response.data
  },

  async renameFile(fileId, newFilename) {
    const response = await apiClient.put(`/files/${fileId}/rename`, {
      new_filename: newFilename
    })
    return response.data
  },

  async checkDuplicate(filename) {
    const response = await apiClient.get(`/files/check-duplicate/${filename}`)
    return response.data
  },

  async listDeletedFiles(page = 1, pageSize = 100) {
    const response = await apiClient.get('/files/deleted', {
      params: { page, page_size: pageSize }
    })
    return response.data
  }
}
