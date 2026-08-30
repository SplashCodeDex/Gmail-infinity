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

  describe('checkAccountsHealth', () => {
    it('posts to the endpoint, indexes results by email, and toasts the summary', async () => {
      mockApi.post.mockResolvedValue({
        data: {
          results: [
            { email: 'a@x.com', status: 'active', message: 'ok' },
            { email: 'b@x.com', status: 'locked', message: 'web login' },
          ],
          summary: { total: 2, active: 1, locked: 1, suspended: 0, password_changed: 0, errors: 0, health_rate: 50 },
        },
      })
      const store = useAppStore()
      const data = await store.checkAccountsHealth()

      expect(mockApi.post).toHaveBeenCalledWith(
        '/accounts/health-check', {}, { timeout: 0 }
      )
      expect(store.healthResults['a@x.com'].status).toBe('active')
      expect(store.healthResults['b@x.com'].status).toBe('locked')
      expect(store.checkingHealth).toBe(false)
      expect(useToastStore().toasts.some(t => t.type === 'success')).toBe(true)
      return data
    })

    it('passes the email subset when given', async () => {
      mockApi.post.mockResolvedValue({
        data: { results: [], summary: { total: 0, active: 0, health_rate: 0 } },
      })
      const store = useAppStore()
      await store.checkAccountsHealth(['a@x.com'])
      expect(mockApi.post).toHaveBeenCalledWith(
        '/accounts/health-check', { emails: ['a@x.com'] }, { timeout: 0 }
      )
    })

    it('rethrows and toasts on failure', async () => {
      mockApi.post.mockRejectedValue({ message: 'boom' })
      const store = useAppStore()
      await expect(store.checkAccountsHealth()).rejects.toThrow('boom')
      expect(useToastStore().toasts.some(t => t.type === 'error')).toBe(true)
      expect(store.checkingHealth).toBe(false)
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

  describe('resumeSession', () => {
    it('calls the resume endpoint, refreshes sessions, and toasts success', async () => {
      mockApi.post.mockResolvedValue({
        data: { session_id: 's_resumed', resumed_from: 's_old', remaining: 3 }
      })
      mockApi.get.mockResolvedValue({ data: { sessions: [] } })
      const store = useAppStore()
      const result = await store.resumeSession('s_old')
      expect(mockApi.post).toHaveBeenCalledWith('/session/s_old/resume')
      expect(result.session_id).toBe('s_resumed')
      expect(result.remaining).toBe(3)
      expect(useToastStore().toasts.some(t => t.type === 'success')).toBe(true)
    })

    it('toasts error and rethrows on failure', async () => {
      mockApi.post.mockRejectedValue({
        response: { data: { detail: 'Session has no remaining accounts' } },
        message: 'Request failed',
      })
      const store = useAppStore()
      await expect(store.resumeSession('s_empty')).rejects.toThrow()
      expect(useToastStore().toasts.some(t => t.type === 'error')).toBe(true)
    })
  })
})
