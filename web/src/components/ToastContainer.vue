<template>
  <div class="fixed bottom-5 right-5 z-50 flex flex-col space-y-2 max-w-sm w-full pointer-events-none px-4 sm:px-0">
    <transition-group
      enter-active-class="transform ease-out duration-300 transition"
      enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
      enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-for="toast in toastStore.toasts"
        :key="toast.id"
        class="pointer-events-auto w-full bg-zinc-900 border border-zinc-800 rounded-xl shadow-lg p-3.5 flex items-start space-x-3 transition-all"
      >
        <!-- Icon -->
        <div class="shrink-0 mt-0.5" :class="getToastIconColor(toast.type)">
          <AppIcon :name="getToastIconName(toast.type)" :size="18" />
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="text-sm font-semibold text-zinc-100">{{ toast.title }}</div>
          <div class="text-xs text-zinc-400 mt-0.5 break-words">{{ toast.message }}</div>
        </div>

        <!-- Dismiss Button -->
        <button
          @click="toastStore.removeToast(toast.id)"
          class="shrink-0 text-zinc-500 hover:text-zinc-300 p-1 rounded transition"
          aria-label="Dismiss notification"
        >
          <AppIcon name="x" :size="14" />
        </button>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { useToastStore } from '../stores/toast'
import AppIcon from './AppIcon.vue'

const toastStore = useToastStore()

function getToastIconColor(type) {
  switch (type) {
    case 'success':
      return 'text-emerald-400'
    case 'error':
      return 'text-rose-400'
    case 'warning':
      return 'text-amber-400'
    case 'info':
    default:
      return 'text-indigo-400'
  }
}

function getToastIconName(type) {
  switch (type) {
    case 'success':
      return 'check-circle'
    case 'error':
      return 'x-circle'
    case 'warning':
      return 'alert-triangle'
    case 'info':
    default:
      return 'info'
  }
}
</script>
