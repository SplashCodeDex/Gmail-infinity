import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useToastStore } from '../toast'

describe('toast store', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('adds a toast with defaults', () => {
    const store = useToastStore()
    const id = store.addToast({ title: 'Hi', message: 'Hello' })
    expect(store.toasts).toHaveLength(1)
    expect(store.toasts[0]).toMatchObject({ id, title: 'Hi', message: 'Hello', type: 'info' })
  })

  it('helper methods set the right type', () => {
    const store = useToastStore()
    store.success('ok')
    store.error('bad')
    store.info('note')
    store.warning('careful')
    expect(store.toasts.map(t => t.type)).toEqual(['success', 'error', 'info', 'warning'])
  })

  it('uses per-type auto-dismiss timings (error/warning linger longer)', () => {
    const store = useToastStore()
    store.success('ok')
    store.warning('careful')
    store.error('bad')
    expect(store.toasts).toHaveLength(3)

    // default 4000ms: success is gone, error/warning still visible
    vi.advanceTimersByTime(4000)
    expect(store.toasts.map(t => t.type).sort()).toEqual(['error', 'warning'])

    // warning uses 5000ms
    vi.advanceTimersByTime(1000)
    expect(store.toasts.map(t => t.type)).toEqual(['error'])

    // error uses 6000ms
    vi.advanceTimersByTime(1000)
    expect(store.toasts).toHaveLength(0)
  })

  it('auto-dismisses after the duration', () => {
    const store = useToastStore()
    store.addToast({ title: 'T', message: 'M', duration: 1000 })
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(1000)
    expect(store.toasts).toHaveLength(0)
  })

  it('duration=0 keeps the toast forever', () => {
    const store = useToastStore()
    store.addToast({ title: 'T', message: 'M', duration: 0 })
    vi.advanceTimersByTime(60_000)
    expect(store.toasts).toHaveLength(1)
  })

  it('removeToast removes only the matching id', () => {
    const store = useToastStore()
    const a = store.addToast({ title: 'A', message: '' })
    store.addToast({ title: 'B', message: '' })
    store.removeToast(a)
    expect(store.toasts).toHaveLength(1)
    expect(store.toasts[0].title).toBe('B')
  })

  it('removeToast is a no-op for unknown ids', () => {
    const store = useToastStore()
    store.addToast({ title: 'A', message: '' })
    expect(() => store.removeToast('does-not-exist')).not.toThrow()
    expect(store.toasts).toHaveLength(1)
  })
})
