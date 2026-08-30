<template>
  <div class="surface-card p-5 flex flex-col h-[400px]">
    <!-- Top Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3.5 mb-3 border-b border-zinc-800 gap-2.5">
      <div class="flex items-center space-x-2.5">
        <div class="w-8 h-8 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-300">
          <AppIcon name="terminal" :size="16" />
        </div>
        <div>
          <h2 class="text-sm font-bold text-zinc-100 flex items-center space-x-2">
            <span>Terminal Output</span>
            <span
              v-if="wsStore.connected"
              class="w-2 h-2 rounded-full bg-emerald-500 ping-indicator"
              title="Pipeline Active"
            ></span>
          </h2>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center space-x-2">
        <button
          @click="autoScroll = !autoScroll"
          class="px-2.5 py-1.5 rounded-lg text-xs font-medium border transition flex items-center space-x-1.5"
          :class="autoScroll ? 'bg-indigo-950/70 border-indigo-800 text-indigo-300' : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:text-zinc-200'"
          title="Toggle Auto Scroll to Bottom"
        >
          <AppIcon name="sliders" :size="13" />
          <span>{{ autoScroll ? 'Scroll: On' : 'Scroll: Paused' }}</span>
        </button>

        <button
          @click="copyLogs"
          :disabled="filteredLogs.length === 0"
          class="px-2.5 py-1.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-xs text-zinc-300 transition flex items-center space-x-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
          title="Copy logs to clipboard"
        >
          <AppIcon name="copy" :size="13" />
          <span>Copy</span>
        </button>

        <button
          @click="clearLogs"
          :disabled="wsStore.logs.length === 0"
          class="px-2.5 py-1.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-xs text-zinc-300 transition flex items-center space-x-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
          title="Clear live log history"
        >
          <AppIcon name="trash-2" :size="13" />
          <span>Clear</span>
        </button>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5 mb-3">
      <!-- Level Tabs -->
      <div class="flex items-center space-x-1 bg-zinc-950/80 p-1 border border-zinc-800 rounded-lg overflow-x-auto">
        <button
          v-for="lvl in LOG_LEVELS"
          :key="lvl.id"
          @click="selectedLevel = lvl.id"
          class="px-2.5 py-1 rounded text-xs font-medium transition shrink-0"
          :class="selectedLevel === lvl.id ? 'bg-zinc-800 text-zinc-100 font-semibold' : 'text-zinc-400 hover:text-zinc-200'"
        >
          {{ lvl.label }}
          <span class="ml-1 text-[10px] opacity-60 font-mono">({{ getCountByLevel(lvl.id) }})</span>
        </button>
      </div>

      <!-- Search Input -->
      <div class="relative w-full sm:w-56">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Filter log stream..."
          class="w-full pl-8 pr-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 font-mono"
        />
        <AppIcon name="search" :size="13" class="absolute left-2.5 top-2 text-zinc-500" />
      </div>
    </div>

    <!-- Terminal Box -->
    <div
      ref="terminalRef"
      class="flex-1 bg-zinc-950 border border-zinc-800/90 rounded-xl p-4 overflow-y-auto font-mono text-xs text-zinc-300 space-y-1.5 selection:bg-zinc-800"
    >
      <div v-if="filteredLogs.length === 0" class="h-full flex flex-col items-center justify-center text-zinc-600">
        <AppIcon name="terminal" :size="28" class="mb-2 opacity-50" />
        <span v-if="wsStore.logs.length === 0">Pipeline listening on WebSocket stream...</span>
        <span v-else>No logs match the current filter criteria</span>
      </div>

      <div
        v-for="log in filteredLogs"
        :key="log.id || log.timestamp"
        class="flex items-start space-x-2 py-0.5 leading-relaxed hover:bg-zinc-900/50 rounded px-1 -mx-1 transition-colors"
      >
        <!-- Timestamp -->
        <span class="text-zinc-500 shrink-0 select-none">
          [{{ formatTime(log.timestamp) }}]
        </span>

        <!-- Icon -->
        <span class="shrink-0 mt-0.5" :class="getLogStyle(log.level).iconColor">
          <AppIcon :name="getLogStyle(log.level).icon" :size="13" />
        </span>

        <!-- Message -->
        <span class="break-all" :class="getLogStyle(log.level).text">
          {{ log.message }}
        </span>
      </div>
    </div>

    <!-- Terminal Footer Status -->
    <div class="mt-2.5 flex items-center justify-between text-[11px] font-mono text-zinc-500 px-1">
      <div class="flex items-center space-x-3">
        <span>Showing {{ filteredLogs.length }} / {{ wsStore.logs.length }} records</span>
        <span v-if="searchQuery" class="text-indigo-400">Search: "{{ searchQuery }}"</span>
      </div>
      <div class="flex items-center space-x-1">
        <span class="w-1.5 h-1.5 rounded-full" :class="wsStore.connected ? 'bg-emerald-500' : 'bg-rose-500'"></span>
        <span>{{ wsStore.connected ? 'WebSocket Online' : 'WebSocket Reconnecting' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useWebSocketStore } from '../stores/websocket'
import { useToastStore } from '../stores/toast'
import { LOG_LEVELS, LOG_STYLES } from '../constants/config'
import AppIcon from './AppIcon.vue'

const wsStore = useWebSocketStore()
const toast = useToastStore()

const terminalRef = ref(null)
const autoScroll = ref(true)
const selectedLevel = ref('all')
const searchQuery = ref('')

const filteredLogs = computed(() => {
  let list = wsStore.logs || []

  if (selectedLevel.value !== 'all') {
    list = list.filter(l => (l.level || 'info').toLowerCase() === selectedLevel.value)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(l => (l.message || '').toLowerCase().includes(q))
  }

  return list
})

function getCountByLevel(levelId) {
  if (levelId === 'all') return wsStore.logs.length
  return wsStore.logs.filter(l => (l.level || 'info').toLowerCase() === levelId).length
}

watch(filteredLogs, async () => {
  if (autoScroll.value) {
    await nextTick()
    if (terminalRef.value) {
      terminalRef.value.scrollTop = terminalRef.value.scrollHeight
    }
  }
}, { deep: true })

function formatTime(timestamp) {
  if (!timestamp) return '00:00:00'
  try {
    const d = new Date(timestamp)
    return d.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return '00:00:00'
  }
}

function getLogStyle(level) {
  const norm = (level || 'info').toLowerCase()
  return LOG_STYLES[norm] || LOG_STYLES.info
}

function clearLogs() {
  wsStore.clearLogs()
  toast.info('Terminal logs cleared', 'Console')
}

async function copyLogs() {
  const text = filteredLogs.value.map(l => `[${formatTime(l.timestamp)}] [${(l.level || 'INFO').toUpperCase()}] ${l.message}`).join('\n')
  try {
    await navigator.clipboard.writeText(text)
    toast.success(`Copied ${filteredLogs.value.length} log lines to clipboard`, 'Copied')
  } catch (err) {
    toast.error('Failed to copy to clipboard', 'Clipboard')
  }
}
</script>
