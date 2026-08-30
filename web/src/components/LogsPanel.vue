<template>
  <div class="surface-card p-5 flex flex-col h-[400px]">
    <!-- Top Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3.5 mb-3 border-b border-zinc-800 gap-2.5">
      <div class="flex items-center space-x-2.5">
        <div class="w-7 h-7 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-300">
          <AppIcon name="terminal" :size="14" />
        </div>
        <h2 class="text-sm font-semibold text-zinc-100">Terminal Output</h2>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center space-x-2">
        <button
          @click="autoScroll = !autoScroll"
          class="px-2.5 py-1 rounded-lg text-xs font-medium border transition flex items-center space-x-1.5"
          :class="autoScroll ? 'bg-zinc-800 border-zinc-700 text-zinc-100' : 'bg-zinc-950 border-zinc-800 text-zinc-500 hover:text-zinc-300'"
          title="Toggle Auto Scroll to Bottom"
        >
          <AppIcon name="sliders" :size="12" />
          <span>{{ autoScroll ? 'Scroll: On' : 'Scroll: Paused' }}</span>
        </button>

        <button
          @click="copyLogs"
          :disabled="filteredLogs.length === 0"
          class="btn-secondary py-1 px-2.5 text-xs flex items-center space-x-1.5"
          title="Copy logs to clipboard"
        >
          <AppIcon name="copy" :size="12" />
          <span>Copy</span>
        </button>

        <button
          @click="clearLogs"
          :disabled="wsStore.logs.length === 0"
          class="btn-secondary py-1 px-2.5 text-xs flex items-center space-x-1.5"
          title="Clear live log history"
        >
          <AppIcon name="trash-2" :size="12" />
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
        </button>
      </div>

      <!-- Search Input -->
      <div class="relative w-full sm:w-56">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Filter log stream..."
          class="w-full pl-8 pr-3 py-1 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 font-mono"
        />
        <AppIcon name="search" :size="12" class="absolute left-2.5 top-1.5 text-zinc-500" />
      </div>
    </div>

    <!-- Terminal Box -->
    <div
      ref="terminalRef"
      class="flex-1 bg-zinc-950 border border-zinc-800/90 rounded-xl p-3.5 overflow-y-auto font-mono text-xs text-zinc-300 space-y-1 selection:bg-zinc-800"
    >
      <div v-if="filteredLogs.length === 0" class="h-full flex flex-col items-center justify-center text-zinc-600">
        <AppIcon name="terminal" :size="24" class="mb-2 opacity-40" />
        <span v-if="wsStore.logs.length === 0">Listening for pipeline events...</span>
        <span v-else>No logs match filter</span>
      </div>

      <div
        v-for="log in filteredLogs"
        :key="log.id || log.timestamp"
        class="flex items-start space-x-2 leading-relaxed hover:bg-zinc-900/50 rounded px-1 -mx-1 transition-colors"
      >
        <!-- Timestamp -->
        <span class="text-zinc-600 shrink-0 select-none">
          {{ formatTime(log.timestamp) }}
        </span>

        <!-- Level Tag -->
        <span class="shrink-0 uppercase text-[11px] font-semibold select-none" :class="getLevelColor(log.level)">
          [{{ (log.level || 'info').slice(0, 4) }}]
        </span>

        <!-- Message -->
        <span class="break-all" :class="getLogStyle(log.level).text">
          {{ log.message }}
        </span>
      </div>
    </div>

    <!-- Terminal Footer Status -->
    <div class="mt-2 flex items-center justify-between text-[11px] font-mono text-zinc-500 px-1">
      <div>Showing {{ filteredLogs.length }} / {{ wsStore.logs.length }} records</div>
      <div v-if="searchQuery" class="text-indigo-400">Search: "{{ searchQuery }}"</div>
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

function getLevelColor(level) {
  const norm = (level || 'info').toLowerCase()
  switch (norm) {
    case 'error': return 'text-rose-400'
    case 'warning': case 'warn': return 'text-amber-400'
    case 'success': return 'text-emerald-400'
    case 'info': default: return 'text-zinc-400'
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
