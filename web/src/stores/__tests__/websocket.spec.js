import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { APP_CONFIG } from '../../constants/config'

class FakeWebSocket {
  static OPEN = 1
  static CONNECTING = 0
  static instances = []

  constructor(url) {
    this.url = url
    this.readyState = FakeWebSocket.CONNECTING
    FakeWebSocket.instances.push(this)
  }

  send() {}
  close() {
    this.readyState = 3
    this.onclose?.()
  }
}

describe('websocket store message handling', () => {
  let store

  beforeEach(() => {
    vi.useFakeTimers()
    setActivePinia(createPinia())
    FakeWebSocket.instances = []
    vi.stubGlobal('WebSocket', FakeWebSocket)
    // happy-dom defaults to http://localhost:3000 — resolveWebSocketUrl() will
    // produce ws://localhost:3000/ws
    return import('../websocket').then(({ useWebSocketStore }) => {
      store = useWebSocketStore()
      store.connect()
      const ws = FakeWebSocket.instances.at(-1)
      ws.readyState = FakeWebSocket.OPEN
      ws.onopen?.()
    })
  })

  afterEach(() => {
    store?.disconnect()
    vi.clearAllTimers()
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  const emit = (payload) => {
    const ws = FakeWebSocket.instances.at(-1)
    ws.onmessage?.({ data: JSON.stringify(payload) })
  }

  it('marks the connection as open', () => {
    expect(store.connected).toBe(true)
    expect(store.isConnecting).toBe(false)
  })

  it('tracks session progress by session_id', () => {
    emit({ type: 'session_progress', session_id: 's1', progress: { successes: 3 } })
    expect(store.sessions.s1).toEqual({ id: 's1', progress: { successes: 3 } })
  })

  it('accumulates created accounts per session', () => {
    emit({ type: 'account_created', session_id: 's1', account: { email: 'a@x.com' } })
    emit({ type: 'account_created', session_id: 's1', account: { email: 'b@x.com' } })
    expect(store.sessions.s1.created_accounts).toEqual([
      { email: 'a@x.com' },
      { email: 'b@x.com' },
    ])
  })

  it('appends session logs and caps history', () => {
    for (let i = 0; i < APP_CONFIG.maxLogHistory + 50; i++) {
      emit({ type: 'session_log', session_id: 's1', log: { level: 'info', message: `m${i}` } })
    }
    expect(store.logs.length).toBe(APP_CONFIG.maxLogHistory)
    expect(store.logs.at(-1).message).toBe(`m${APP_CONFIG.maxLogHistory + 49}`)
  })

  it('ignores non-JSON messages without throwing', () => {
    const ws = FakeWebSocket.instances.at(-1)
    expect(() => ws.onmessage?.({ data: 'not json' })).not.toThrow()
  })

  it('records final status on session_complete', () => {
    emit({ type: 'session_complete', session_id: 's2', status: 'completed', progress: { successes: 9 } })
    expect(store.sessions.s2).toMatchObject({ status: 'completed', progress: { successes: 9 } })
  })

  it('does not reconnect while already open', () => {
    const before = FakeWebSocket.instances.length
    store.connect()
    expect(FakeWebSocket.instances.length).toBe(before)
  })
})
