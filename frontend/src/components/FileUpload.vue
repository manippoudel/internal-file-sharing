<template>
  <div class="file-upload">
    <div class="upload-header">
      <h2>Upload Files</h2>
      <button @click="$emit('close')" class="close-btn">×</button>
    </div>
    
    <div id="uppy-dashboard"></div>
    
    <div v-if="uploadStatus" class="upload-status" :class="uploadStatus.type">
      {{ uploadStatus.message }}
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import Uppy from '@uppy/core';
import Dashboard from '@uppy/dashboard';
// Import CSS via CDN or comment out if causing issues
// import '@uppy/core/dist/style.css';
// import '@uppy/dashboard/dist/style.css';
import uploadService from '../services/uploadService';
import { useFileStore } from '../stores/files';
import CryptoJS from 'crypto-js';

export default {
  name: 'FileUpload',
  emits: ['close', 'upload-complete'],
  setup(props, { emit }) {
    const filesStore = useFileStore();
    const uploadStatus = ref(null);
    let uppy = null;

    const CHUNK_SIZE = 50 * 1024 * 1024; // 50MB chunks

    onMounted(async () => {
      // Get auth token
      const token = localStorage.getItem('auth_token');
      
      // Initialize Uppy
      uppy = new Uppy({
        restrictions: {
          maxNumberOfFiles: 10,
          maxFileSize: 10 * 1024 * 1024 * 1024, // 10GB
        },
        autoProceed: false,
      });

      // Add Dashboard plugin
      uppy.use(Dashboard, {
        target: '#uppy-dashboard',
        inline: true,
        height: 400,
        showProgressDetails: true,
        proudlyDisplayPoweredByUppy: false,
        note: 'Files up to 10GB, maximum 10 files at a time',
      });

      // Handle file addition
      uppy.on('file-added', async (file) => {
        try {
          // Check for duplicates
          const duplicate = await uploadService.checkDuplicate(file.name);
          if (duplicate.exists) {
            const confirmUpload = confirm(
              `A file named "${file.name}" already exists. Do you want to upload anyway?`
            );
            if (!confirmUpload) {
              uppy.removeFile(file.id);
              return;
            }
          }

          // Initialize chunked upload
          const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
          const initResponse = await uploadService.initializeUpload(
            file.name,
            file.size,
            totalChunks
          );

          // Store upload ID in file meta
          uppy.setFileMeta(file.id, {
            uploadId: initResponse.upload_id,
            totalChunks: totalChunks,
            chunkSize: CHUNK_SIZE
          });

          uploadStatus.value = {
            type: 'info',
            message: `Initialized upload for ${file.name}`
          };
        } catch (error) {
          console.error('Error initializing upload:', error);
          uploadStatus.value = {
            type: 'error',
            message: `Failed to initialize upload: ${error.response?.data?.detail || error.message}`
          };
          uppy.removeFile(file.id);
        }
      });

      // Manual chunked upload on button click
      uppy.on('upload', async () => {
        const files = uppy.getFiles();
        
        for (const file of files) {
          try {
            uppy.emit('upload-started', file);
            const uploadId = file.meta.uploadId;
            const totalChunks = file.meta.totalChunks;
            const chunkSize = file.meta.chunkSize;
            
            // Upload chunks
            for (let i = 0; i < totalChunks; i++) {
              const start = i * chunkSize;
              const end = Math.min(start + chunkSize, file.size);
              const chunk = file.data.slice(start, end);
              
              // Calculate checksum for chunk
              const reader = new FileReader();
              const checksum = await new Promise((resolve) => {
                reader.onload = (e) => {
                  const wordArray = CryptoJS.lib.WordArray.create(e.target.result);
                  resolve(CryptoJS.SHA256(wordArray).toString());
                };
                reader.readAsArrayBuffer(chunk);
              });
              
              // Upload chunk
              await uploadService.uploadChunk(
                uploadId,
                i,
                chunk,
                checksum,
                file.name,
                totalChunks
              );
              
              // Update progress
              const progress = ((i + 1) / totalChunks) * 100;
              uppy.emit('upload-progress', file, {
                uploader: uppy,
                bytesUploaded: end,
                bytesTotal: file.size
              });
            }
            
            // Calculate final checksum of entire file
            const finalChecksumReader = new FileReader();
            const finalChecksum = await new Promise((resolve) => {
              finalChecksumReader.onload = (e) => {
                const wordArray = CryptoJS.lib.WordArray.create(e.target.result);
                resolve(CryptoJS.SHA256(wordArray).toString());
              };
              finalChecksumReader.readAsArrayBuffer(file.data);
            });
            
            // Complete upload
            await uploadService.completeUpload(uploadId, finalChecksum);
            
            uppy.emit('upload-success', file, {});
            
            uploadStatus.value = {
              type: 'success',
              message: `Successfully uploaded ${file.name}`
            };
            
            // Refresh file list
            await filesStore.fetchFiles();
            
          } catch (error) {
            console.error('Upload error:', error);
            uppy.emit('upload-error', file, error);
            uploadStatus.value = {
              type: 'error',
              message: `Upload failed: ${error.response?.data?.detail || error.message}`
            };
          }
        }
        
        setTimeout(() => {
          emit('upload-complete');
        }, 2000);
      });

      // Handle upload error
      uppy.on('upload-error', (file, error) => {
        console.error('Upload error:', error);
        uploadStatus.value = {
          type: 'error',
          message: `Upload failed: ${error.message}`
        };
      });

      // Handle file removal
      uppy.on('file-removed', async (file) => {
        if (file.meta.uploadId) {
          try {
            await uploadService.cancelUpload(file.meta.uploadId);
          } catch (error) {
            console.error('Error canceling upload:', error);
          }
        }
      });
    });

    onBeforeUnmount(() => {
      if (uppy) {
        uppy.cancelAll();
        uppy = null;
      }
    });

    return {
      uploadStatus
    };
  }
};
</script>

<style scoped>
.file-upload {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.upload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.upload-header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 32px;
  cursor: pointer;
  color: #999;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
}

.close-btn:hover {
  color: #333;
}

#uppy-dashboard {
  margin: 20px 0;
}

.upload-status {
  padding: 12px 16px;
  border-radius: 4px;
  margin-top: 16px;
  font-size: 14px;
}

.upload-status.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.upload-status.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.upload-status.info {
  background-color: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}
</style>
