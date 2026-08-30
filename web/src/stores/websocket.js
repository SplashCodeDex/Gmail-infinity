import { defineStore } from 'pinia'
import { ref } from 'vue'
import { APP_CONFIG } from '../constants/config'

const resolveWebSocketUrl = () => {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL
  }
  const isSecure = window.location.protocol === 'https:'
  const protocol = isSecure ? 'wss:' : 'ws:'
  const host = window.location.host || 'localhost:3000'
  return `${protocol}//${host}/ws`
}

export const useWebSocketStore = defineStore('websocket', () => {
  const ws = ref(null)
  const connected = ref(false)
  const isConnecting = ref(false)
  const logs = ref([])
  const sessions = ref({})
  const reconnectAttempts = ref(0)
  let reconnectTimeout = null

  function connect() {
    if (ws.value && (ws.value.readyState === WebSocket.OPEN || ws.value.readyState === WebSocket.CONNECTING)) {
      return
    }

    isConnecting.value = true
    const wsUrl = resolveWebSocketUrl()

    try {
      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        connected.value = true
        isConnecting.value = false
        reconnectAttempts.value = 0
        console.log('[WS] Connected to live pipeline:', wsUrl)

        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout)
          reconnectTimeout = null
        }
      }

      ws.value.onclose = () => {
        connected.value = false
        isConnecting.value = false
        ws.value = null
        reconnectAttempts.value += 1

        const delay = Math.min(1000 * Math.pow(1.5, reconnectAttempts.value), 10000)
        reconnectTimeout = setTimeout(() => {
          connect()
        }, delay)
      }

      ws.value.onerror = (err) => {
        console.warn('[WS] Stream error:', err)
        ws.value?.close()
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleMessage(data)
        } catch {
          // Ignore non-JSON ping/debug messages
        }
      }
    } catch (e) {
      console.error('[WS] Connection init error:', e)
      isConnecting.value = false
      reconnectTimeout = setTimeout(connect, 3000)
    }
  }

  function handleMessage(data) {
    switch (data.type) {
      case 'session_log':
        if (data.log) {
          logs.value.push({
            id: Date.now() + Math.random().toString(36).slice(2, 6),
            ...data.log,
          })
          if (logs.value.length > APP_CONFIG.maxLogHistory) {
            logs.value.shift()
          }
        }
        break

      case 'session_progress':
        if (data.session_id) {
          if (!sessions.value[data.session_id]) {
            sessions.value[data.session_id] = { id: data.session_id }
          }
          sessions.value[data.session_id].progress = data.progress
        }
        break

      case 'account_created':
        if (data.session_id) {
          if (!sessions.value[data.session_id]) {
            sessions.value[data.session_id] = { id: data.session_id, created_accounts: [] }
          }
          if (!sessions.value[data.session_id].created_accounts) {
            sessions.value[data.session_id].created_accounts = []
          }
          sessions.value[data.session_id].created_accounts.push(data.account)
        }
        break

      case 'session_complete':
        if (data.session_id) {
          if (!sessions.value[data.session_id]) {
            sessions.value[data.session_id] = { id: data.session_id }
          }
          sessions.value[data.session_id].status = data.status
          sessions.value[data.session_id].progress = data.progress
        }
        break
    }
  }

  function clearLogs() {
    logs.value = []
  }

  function send(data) {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }

  function disconnect() {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    connected.value = false
    isConnecting.value = false
  }

  return {
    ws,
    connected,
    isConnecting,
    logs,
    sessions,
    reconnectAttempts,
    connect,
    clearLogs,
    send,
    disconnect,
  }
})
