import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api'
})

export const useAppStore = defineStore('app', () => {
  const stats = ref({})
  const config = ref({})
  const accounts = ref([])
  const sessions = ref([])
  const loading = ref(false)

  async function fetchStats() {
    const { data } = await api.get('/stats')
    stats.value = data
  }

  async function fetchConfig() {
    const { data } = await api.get('/config')
    config.value = data
  }

  async function fetchAccounts() {
    const { data } = await api.get('/accounts')
    accounts.value = data.accounts
  }

  async function fetchSessions() {
    const { data } = await api.get('/sessions')
    sessions.value = data.sessions
  }

  async function startSession(sessionConfig) {
    loading.value = true
    try {
      const { data } = await api.post('/session/start', sessionConfig)
      await fetchSessions()
      return data
    } finally {
      loading.value = false
    }
  }

  async function stopSession(sessionId) {
    await api.post(`/session/${sessionId}/stop`)
    await fetchSessions()
  }

  async function exportAccounts(format) {
    const response = await api.post('/accounts/export', { format }, {
      responseType: 'blob'
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `accounts_${Date.now()}.${format}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  }

  async function testProxies() {
    const { data } = await api.post('/proxies/test')
    await fetchStats()
    return data.results
  }

  return {
    stats,
    config,
    accounts,
    sessions,
    loading,
    fetchStats,
    fetchConfig,
    fetchAccounts,
    fetchSessions,
    startSession,
    stopSession,
    exportAccounts,
    testProxies
  }
})
