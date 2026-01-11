import api from './api';

class UploadService {
  /**
   * Initialize a chunked upload
   */
  async initializeUpload(filename, fileSize, totalChunks) {
    const response = await api.post('/files/upload/init', {
      filename,
      file_size: fileSize,
      total_chunks: totalChunks
    });
    return response.data;
  }

  /**
   * Upload a single chunk
   */
  async uploadChunk(uploadId, chunkIndex, chunkData) {
    const formData = new FormData();
    formData.append('chunk', chunkData);
    
    const response = await api.post(
      `/files/upload/chunk?upload_id=${uploadId}&chunk_index=${chunkIndex}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    return response.data;
  }

  /**
   * Complete the chunked upload
   */
  async completeUpload(uploadId, checksum) {
    const response = await api.post('/files/upload/complete', {
      upload_id: uploadId,
      checksum: checksum
    });
    return response.data;
  }

  /**
   * Cancel an ongoing upload
   */
  async cancelUpload(uploadId) {
    const response = await api.post('/files/upload/cancel', {
      upload_id: uploadId
    });
    return response.data;
  }

  /**
   * Check if a file with the same name already exists
   */
  async checkDuplicate(filename) {
    const response = await api.get(`/files/check-duplicate/${encodeURIComponent(filename)}`);
    return response.data;
  }
}

export default new UploadService();
