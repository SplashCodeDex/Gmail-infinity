import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])

  function addToast({ title, message, type = 'info', duration = 4000 }) {
    const id = Date.now() + Math.random().toString(36).slice(2, 7)
    const toast = { id, title, message, type }
    toasts.value.push(toast)

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }
    return id
  }

  function removeToast(id) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }

  function success(message, title = 'Success') {
    return addToast({ title, message, type: 'success' })
  }

  function error(message, title = 'Error') {
    return addToast({ title, message, type: 'error', duration: 6000 })
  }

  function info(message, title = 'Notice') {
    return addToast({ title, message, type: 'info' })
  }

  function warning(message, title = 'Warning') {
    return addToast({ title, message, type: 'warning', duration: 5000 })
  }

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    info,
    warning,
  }
})
