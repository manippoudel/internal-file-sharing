/**
 * Tests for files store
 *
 * Tests cover:
 * - Fetch files from API
 * - Pagination
 * - Search and sorting
 * - Delete and restore files
 * - File selection
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFilesStore } from '../../src/stores/files'
import axios from 'axios'

// Mock axios
vi.mock('axios')

describe('Files Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should initialize with default state', () => {
    const store = useFilesStore()

    expect(store.files).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.page).toBe(1)
    expect(store.selectedFiles).toEqual([])
  })

  it('should fetch files successfully', async () => {
    const store = useFilesStore()
    const mockFiles = [
      { id: '1', filename: 'file1.txt', size: 1000 },
      { id: '2', filename: 'file2.txt', size: 2000 },
    ]

    axios.get.mockResolvedValueOnce({
      data: {
        files: mockFiles,
        total: 2,
        page: 1,
        totalPages: 1,
      },
    })

    await store.fetchFiles()

    expect(store.files).toEqual(mockFiles)
    expect(store.loading).toBe(false)
  })

  it('should handle fetch error', async () => {
    const store = useFilesStore()

    axios.get.mockRejectedValueOnce(new Error('Network error'))

    await store.fetchFiles()

    expect(store.error).toBeTruthy()
    expect(store.files).toEqual([])
  })

  it('should delete file', async () => {
    const store = useFilesStore()
    const fileId = 'test-file-id'

    axios.post.mockResolvedValueOnce({ data: { message: 'Deleted' } })

    await store.deleteFile(fileId)

    expect(axios.post).toHaveBeenCalledWith(
      `/api/v1/files/${fileId}/delete`,
      expect.anything()
    )
  })

  it('should restore file', async () => {
    const store = useFilesStore()
    const fileId = 'test-file-id'

    axios.post.mockResolvedValueOnce({ data: { message: 'Restored' } })

    await store.restoreFile(fileId)

    expect(axios.post).toHaveBeenCalledWith(
      `/api/v1/files/${fileId}/restore`,
      expect.anything()
    )
  })

  it('should rename file', async () => {
    const store = useFilesStore()
    const fileId = 'test-file-id'
    const newFilename = 'renamed.txt'

    axios.post.mockResolvedValueOnce({ data: { filename: newFilename } })

    await store.renameFile(fileId, newFilename)

    expect(axios.post).toHaveBeenCalledWith(
      `/api/v1/files/${fileId}/rename`,
      expect.objectContaining({ new_filename: newFilename })
    )
  })

  it('should toggle file selection', () => {
    const store = useFilesStore()
    const file = { id: '1', filename: 'test.txt' }

    // Select file
    store.toggleFileSelection(file)
    expect(store.selectedFiles).toContain(file)

    // Deselect file
    store.toggleFileSelection(file)
    expect(store.selectedFiles).not.toContain(file)
  })

  it('should select all files', () => {
    const store = useFilesStore()
    store.files = [
      { id: '1', filename: 'file1.txt' },
      { id: '2', filename: 'file2.txt' },
    ]

    store.selectAll()

    expect(store.selectedFiles.length).toBe(2)
  })

  it('should clear selection', () => {
    const store = useFilesStore()
    store.selectedFiles = [
      { id: '1', filename: 'file1.txt' },
      { id: '2', filename: 'file2.txt' },
    ]

    store.clearSelection()

    expect(store.selectedFiles).toEqual([])
  })

  it('should set page and refetch', async () => {
    const store = useFilesStore()

    axios.get.mockResolvedValue({
      data: { files: [], total: 0, page: 2, totalPages: 5 },
    })

    await store.setPage(2)

    expect(store.page).toBe(2)
    expect(axios.get).toHaveBeenCalled()
  })

  it('should set sort order', async () => {
    const store = useFilesStore()

    axios.get.mockResolvedValue({
      data: { files: [], total: 0 },
    })

    await store.setSort('filename', 'asc')

    expect(store.sortBy).toBe('filename')
    expect(store.sortOrder).toBe('asc')
  })

  it('should set search query', async () => {
    const store = useFilesStore()

    axios.get.mockResolvedValue({
      data: { files: [], total: 0 },
    })

    await store.setSearch('test query')

    expect(store.searchQuery).toBe('test query')
  })

  it('should download file', async () => {
    const store = useFilesStore()
    const fileId = 'test-file-id'

    // Mock blob response
    axios.get.mockResolvedValueOnce({
      data: new Blob(['file content']),
      headers: { 'content-disposition': 'attachment; filename="test.txt"' },
    })

    await store.downloadFile(fileId)

    expect(axios.get).toHaveBeenCalledWith(
      `/api/v1/files/${fileId}/download`,
      expect.objectContaining({ responseType: 'blob' })
    )
  })

  it('should bulk download files', async () => {
    const store = useFilesStore()
    store.selectedFiles = [
      { id: '1', filename: 'file1.txt' },
      { id: '2', filename: 'file2.txt' },
    ]

    axios.post.mockResolvedValueOnce({
      data: new Blob(['zip content']),
    })

    await store.bulkDownload()

    expect(axios.post).toHaveBeenCalledWith(
      '/api/v1/files/download/bulk',
      expect.objectContaining({ file_ids: ['1', '2'] }),
      expect.any(Object)
    )
  })
})
