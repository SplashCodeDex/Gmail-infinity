import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWebSocketStore = defineStore('websocket', () => {
  const ws = ref(null)
  const connected = ref(false)
  const logs = ref([])
  const sessions = ref({})
  let reconnectTimeout = null

  function connect() {
    if (ws.value && (ws.value.readyState === WebSocket.OPEN || ws.value.readyState === WebSocket.CONNECTING)) {
      return
    }

    const wsUrl = `ws://${window.location.hostname || 'localhost'}:8000/ws`
    try {
      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        connected.value = true
        console.log('[WS] Connected to FastAPI backend:', wsUrl)
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout)
          reconnectTimeout = null
        }
      }

      ws.value.onclose = () => {
        connected.value = false
        console.log('[WS] Disconnected from FastAPI backend. Reconnecting in 3s...')
        ws.value = null
        reconnectTimeout = setTimeout(() => {
          connect()
        }, 3000)
      }

      ws.value.onerror = (err) => {
        console.error('[WS] WebSocket error:', err)
        ws.value?.close()
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleMessage(data)
        } catch (e) {
          console.debug('[WS] Non-JSON message received:', event.data)
        }
      }
    } catch (e) {
      console.error('[WS] Connection failed:', e)
      reconnectTimeout = setTimeout(connect, 3000)
    }
  }

  function handleMessage(data) {
    switch (data.type) {
      case 'session_log':
        if (data.log) {
          logs.value.push(data.log)
          if (logs.value.length > 200) logs.value.shift()
        }
        break

      case 'session_progress':
        if (data.session_id && sessions.value[data.session_id]) {
          sessions.value[data.session_id].progress = data.progress
        }
        break

      case 'account_created':
        if (data.session_id && sessions.value[data.session_id]) {
          if (!sessions.value[data.session_id].created_accounts) {
            sessions.value[data.session_id].created_accounts = []
          }
          sessions.value[data.session_id].created_accounts.push(data.account)
        }
        break

      case 'session_complete':
        if (data.session_id && sessions.value[data.session_id]) {
          sessions.value[data.session_id].status = data.status
          sessions.value[data.session_id].progress = data.progress
        }
        break
    }
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
  }

  return {
    ws,
    connected,
    logs,
    sessions,
    connect,
    send,
    disconnect
  }
})
