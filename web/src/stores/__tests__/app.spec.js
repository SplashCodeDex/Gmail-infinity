import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

// app.js calls axios.create() at module load — mock it before the import runs
const mockApi = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}))
vi.mock('axios', () => ({
  default: { create: vi.fn(() => mockApi) },
}))

import { useAppStore } from '../app'
import { useToastStore } from '../toast'

describe('app store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.resetAllMocks()
  })

  describe('fetchStats', () => {
    it('stores the response payload', async () => {
      mockApi.get.mockResolvedValue({ data: { accounts: { total: 7 } } })
      const store = useAppStore()
      await store.fetchStats()
      expect(mockApi.get).toHaveBeenCalledWith('/stats')
      expect(store.stats.accounts.total).toBe(7)
      expect(store.lastUpdated).not.toBeNull()
    })

    it('does not throw when the API fails', async () => {
      mockApi.get.mockRejectedValue(new Error('down'))
      const store = useAppStore()
      await expect(store.fetchStats()).resolves.toBeUndefined()
    })
  })

  describe('startSession', () => {
    it('posts the config and refreshes data', async () => {
      mockApi.post.mockResolvedValue({ data: { session_id: 's1' } })
      mockApi.get.mockResolvedValue({ data: { sessions: [] } })
      const store = useAppStore()
      const result = await store.startSession({ num_accounts: 5 })
      expect(mockApi.post).toHaveBeenCalledWith('/session/start', { num_accounts: 5 })
      expect(result.session_id).toBe('s1')
      expect(store.loading).toBe(false)
    })

    it('toasts and rethrows on failure', async () => {
      mockApi.post.mockRejectedValue({
        response: { data: { detail: 'bad config' } },
        message: 'Request failed',
      })
      const store = useAppStore()
      await expect(store.startSession({})).rejects.toThrow()
      expect(useToastStore().toasts.some(t => t.type === 'error')).toBe(true)
      expect(store.loading).toBe(false)
    })
  })

  describe('exportAccounts (blob URL lifecycle)', () => {
    const blobResponse = () => ({ data: new Blob(['email,pass'], { type: 'text/csv' }) })

    it('revokes the object URL after a successful download', async () => {
      const createObjectURL = vi.fn(() => 'blob:mock')
      const revokeObjectURL = vi.fn()
      vi.stubGlobal('URL', { ...window.URL, createObjectURL, revokeObjectURL })

      mockApi.post.mockResolvedValue(blobResponse())
      const store = useAppStore()
      await store.exportAccounts('csv')

      expect(mockApi.post).toHaveBeenCalledWith('/accounts/export', { format: 'csv' }, { responseType: 'blob' })
      expect(createObjectURL).toHaveBeenCalledTimes(1)
      expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock')
      vi.unstubAllGlobals()
    })

    it('revokes the object URL even when the download path throws', async () => {
      const createObjectURL = vi.fn(() => 'blob:mock')
      const revokeObjectURL = vi.fn()
      vi.stubGlobal('URL', { ...window.URL, createObjectURL, revokeObjectURL })

      mockApi.post.mockResolvedValue(blobResponse())
      const store = useAppStore()
      // Force an error after the URL was created (toast failure path)
      const toastSpy = vi.spyOn(useToastStore(), 'success').mockImplementation(() => {
        throw new Error('toast exploded')
      })

      await expect(store.exportAccounts('csv')).rejects.toThrow('toast exploded')
      expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock')
      toastSpy.mockRestore()
      vi.unstubAllGlobals()
    })

    it('surfaces the server error when a JSON error body arrives as a blob', async () => {
      const errorBody = JSON.stringify({ detail: 'Export failed: disk full' })
      mockApi.post.mockResolvedValue({
        data: new Blob([errorBody], { type: 'application/json' }),
      })
      const createObjectURL = vi.fn()
      const revokeObjectURL = vi.fn()
      vi.stubGlobal('URL', { ...window.URL, createObjectURL, revokeObjectURL })

      const store = useAppStore()
      await expect(store.exportAccounts('json')).rejects.toThrow('Export failed: disk full')
      expect(createObjectURL).not.toHaveBeenCalled()
      expect(revokeObjectURL).not.toHaveBeenCalled()
      vi.unstubAllGlobals()
    })
  })
})
