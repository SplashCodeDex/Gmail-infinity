import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { useToastStore } from './toast'

// Dynamic API Base URL: fallback to '/api' for Vite proxy or env override
const resolveApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  return '/api'
}

const api = axios.create({
  baseURL: resolveApiBaseUrl(),
  timeout: 30000,
})

export const useAppStore = defineStore('app', () => {
  const stats = ref({
    accounts: { total: 0, successes: 0, failures: 0, success_rate: 0 },
    proxies: { total: 0, healthy: 0, unhealthy: 0 },
    active_sessions: 0,
  })
  const config = ref({})
  const accounts = ref([])
  const sessions = ref([])
  const loading = ref(false)
  const isRefreshing = ref(false)
  const lastUpdated = ref(null)
  const checkingHealth = ref(false)
  const healthResults = ref({})

  const toast = useToastStore()

  async function fetchStats() {
    try {
      const { data } = await api.get('/stats')
      stats.value = data
      lastUpdated.value = new Date()
    } catch (error) {
      console.error('[Store] Failed to fetch stats:', error)
    }
  }

  async function fetchConfig() {
    try {
      const { data } = await api.get('/config')
      config.value = data
    } catch (error) {
      console.error('[Store] Failed to fetch config:', error)
    }
  }

  async function fetchAccounts() {
    try {
      const { data } = await api.get('/accounts')
      accounts.value = data.accounts || []
    } catch (error) {
      console.error('[Store] Failed to fetch accounts:', error)
      toast.error(error.response?.data?.detail || error.message, 'Failed to Load Accounts')
    }
  }

  async function fetchSessions() {
    try {
      const { data } = await api.get('/sessions')
      sessions.value = data.sessions || []
    } catch (error) {
      console.error('[Store] Failed to fetch sessions:', error)
    }
  }

  async function refreshAll() {
    if (isRefreshing.value) return
    isRefreshing.value = true
    try {
      await Promise.allSettled([
        fetchStats(),
        fetchConfig(),
        fetchSessions(),
        fetchAccounts(),
      ])
    } finally {
      isRefreshing.value = false
    }
  }

  async function startSession(sessionConfig) {
    loading.value = true
    try {
      const { data } = await api.post('/session/start', sessionConfig)
      await fetchSessions()
      await fetchStats()
      toast.success(`Session started: ${data.session_id}`, 'Engine Launch')
      return data
    } catch (error) {
      const msg = error.response?.data?.detail || error.message
      toast.error(msg, 'Failed to Start Session')
      throw error
    } finally {
      loading.value = false
    }
  }

  async function stopSession(sessionId) {
    try {
      await api.post(`/session/${sessionId}/stop`)
      await fetchSessions()
      await fetchStats()
      toast.info(`Session ${sessionId} has been stopped`, 'Session Halted')
    } catch (error) {
      const msg = error.response?.data?.detail || error.message
      toast.error(msg, 'Failed to Stop Session')
      throw error
    }
  }

  async function resumeSession(sessionId) {
    try {
      const { data } = await api.post(`/session/${sessionId}/resume`)
      await fetchSessions()
      await fetchStats()
      toast.success(`Resumed session: ${data.session_id} (${data.remaining} remaining)`, 'Session Resumed')
      return data
    } catch (error) {
      const msg = error.response?.data?.detail || error.message
      toast.error(msg, 'Failed to Resume Session')
      throw error
    }
  }

  async function exportAccounts(format = 'json') {
    let url = null
    try {
      const response = await api.post('/accounts/export', { format }, {
        responseType: 'blob',
      })

      // If the server returned a JSON error body, axios still hands us a blob —
      // surface the real error message instead of "downloading" it.
      if (response.data?.type === 'application/json') {
        const text = await response.data.text()
        let detail = text
        try {
          detail = JSON.parse(text)?.detail || text
        } catch { /* keep raw text */ }
        throw new Error(detail)
      }

      url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `gmail_infinity_accounts_${Date.now()}.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()

      toast.success(`Exported accounts as ${format.toUpperCase()}`, 'Export Completed')
    } catch (error) {
      const msg = error.response?.data?.detail || error.message
      toast.error(msg, 'Export Failed')
      throw error
    } finally {
      // Always release the blob URL, even if click()/toast throws.
      if (url) window.URL.revokeObjectURL(url)
    }
  }

  async function checkAccountsHealth(emails = null) {
    checkingHealth.value = true
    try {
      // IMAP checks are slow — disable the axios timeout for this call
      const { data } = await api.post(
        '/accounts/health-check',
        emails ? { emails } : {},
        { timeout: 0 }
      )
      const map = { ...healthResults.value }
      for (const r of data.results) map[r.email] = r
      healthResults.value = map

      const s = data.summary
      if (s.total === 0) {
        toast.info('No accounts with stored passwords to check', 'Account Health')
      } else {
        toast.success(
          `${s.active}/${s.total} active (${Math.round(s.health_rate)}%) — ` +
          `${s.locked} locked, ${s.suspended} suspended, ${s.password_changed} pw-changed`,
          'Account Health'
        )
      }
      return data
    } catch (error) {
      const msg = error.response?.data?.detail || error.message
      toast.error(msg, 'Health Check Failed')
      throw error
    } finally {
      checkingHealth.value = false
    }
  }

  async function testProxies() {
    try {
      const { data } = await api.post('/proxies/test')
      await fetchStats()
      toast.success(`Tested ${data.results?.total || 0} proxies (${data.results?.healthy || 0} healthy)`, 'Proxy Health Check')
      return data.results
    } catch (error) {
      const msg = error.response?.data?.detail || error.message
      toast.error(msg, 'Proxy Health Test Failed')
      throw error
    }
  }

  async function importProxies(proxyList, replace = false) {
    try {
      const proxies = Array.isArray(proxyList)
        ? proxyList
        : proxyList.split('\n').map(l => l.trim()).filter(Boolean)
      const { data } = await api.post('/proxies/import', { proxies, replace })
      await fetchStats()
      toast.success(`Imported ${data.added} proxies (Total: ${data.total})`, 'Proxies Saved')
      return data
    } catch (error) {
      const msg = error.response?.data?.detail || error.message
      toast.error(msg, 'Proxy Import Failed')
      throw error
    }
  }

  async function fetchPublicProxies() {
    try {
      const { data } = await api.post('/proxies/fetch')
      await fetchStats()
      toast.success(`Fetched ${data.fetched} public proxies (${data.added} new added)`, 'Public Proxy Pool')
      return data
    } catch (error) {
      const msg = error.response?.data?.detail || error.message
      toast.error(msg, 'Proxy Fetch Failed')
      throw error
    }
  }

  async function clearProxies() {
    try {
      await api.post('/proxies/clear')
      await fetchStats()
      toast.info('Proxy pool has been cleared', 'Proxy Pool')
    } catch (error) {
      const msg = error.response?.data?.detail || error.message
      toast.error(msg, 'Failed to clear proxies')
      throw error
    }
  }

  async function fetchProxiesList() {
    try {
      const { data } = await api.get('/proxies')
      return data
    } catch (error) {
      console.error('[Store] Failed to fetch proxies list:', error)
      return { total: 0, healthy: 0, unhealthy: 0, list: [] }
    }
  }

  async function fetchSmsBalances() {
    try {
      const { data } = await api.get('/sms/balances')
      return data.balances || {}
    } catch (error) {
      console.error('[Store] Failed to fetch SMS balances:', error)
      return {}
    }
  }

  async function testTelegram() {
    try {
      const { data } = await api.post('/telegram/test')
      if (data.success) {
        toast.success(data.message || 'Telegram test message sent!', 'Telegram Bot')
      } else {
        toast.warning(data.message || 'Telegram delivery failed', 'Telegram Bot')
      }
      return data
    } catch (error) {
      const msg = error.response?.data?.detail || error.message
      toast.error(msg, 'Telegram Test Failed')
      throw error
    }
  }

  async function fetchEngineCapabilities() {
    try {
      const { data } = await api.get('/engine/capabilities')
      return data
    } catch (error) {
      console.error('[Store] Failed to fetch engine capabilities:', error)
      return null
    }
  }

  return {
    stats,
    config,
    accounts,
    sessions,
    loading,
    isRefreshing,
    lastUpdated,
    checkingHealth,
    healthResults,
    fetchStats,
    fetchConfig,
    fetchAccounts,
    fetchSessions,
    refreshAll,
    startSession,
    stopSession,
    resumeSession,
    exportAccounts,
    checkAccountsHealth,
    testProxies,
    importProxies,
    fetchPublicProxies,
    clearProxies,
    fetchProxiesList,
    fetchSmsBalances,
    testTelegram,
    fetchEngineCapabilities,
  }
})

