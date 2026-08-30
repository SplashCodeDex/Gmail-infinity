<template>
  <div class="surface-card p-4 flex flex-col h-[400px] space-y-3">
    <!-- Single Consolidated Toolbar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-zinc-800 gap-2.5">
      <!-- Left: Title & Level Filter -->
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <div class="w-6 h-6 rounded-md bg-zinc-800 flex items-center justify-center text-zinc-300">
            <AppIcon name="terminal" :size="13" />
          </div>
          <h2 class="text-xs font-semibold text-zinc-100 uppercase tracking-wider">Terminal</h2>
        </div>

        <div class="flex items-center space-x-1 bg-zinc-950/80 p-0.5 border border-zinc-800 rounded-lg">
          <button
            v-for="lvl in LOG_LEVELS"
            :key="lvl.id"
            @click="selectedLevel = lvl.id"
            class="px-2 py-0.5 rounded text-[11px] font-medium transition shrink-0"
            :class="selectedLevel === lvl.id ? 'bg-zinc-800 text-zinc-100 font-semibold' : 'text-zinc-400 hover:text-zinc-200'"
          >
            {{ lvl.label }}
          </button>
        </div>
      </div>

      <!-- Right: Search & Actions -->
      <div class="flex items-center space-x-1.5">
        <div class="relative w-36 sm:w-44">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Filter logs..."
            class="w-full pl-7 pr-2.5 py-1 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 font-mono"
          />
          <AppIcon name="search" :size="11" class="absolute left-2 top-1.5 text-zinc-500" />
        </div>

        <button
          @click="autoScroll = !autoScroll"
          class="p-1 rounded-lg border transition text-xs"
          :class="autoScroll ? 'bg-zinc-800 border-zinc-700 text-zinc-100' : 'bg-zinc-950 border-zinc-800 text-zinc-500 hover:text-zinc-300'"
          :title="autoScroll ? 'Auto-scroll is on' : 'Auto-scroll is paused'"
        >
          <AppIcon name="sliders" :size="13" />
        </button>

        <button
          @click="copyLogs"
          :disabled="filteredLogs.length === 0"
          class="p-1 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-zinc-300 transition disabled:opacity-50"
          title="Copy logs"
        >
          <AppIcon name="copy" :size="13" />
        </button>

        <button
          @click="clearLogs"
          :disabled="wsStore.logs.length === 0"
          class="p-1 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-zinc-300 transition disabled:opacity-50"
          title="Clear terminal"
        >
          <AppIcon name="trash-2" :size="13" />
        </button>
      </div>
    </div>

    <!-- Terminal Box -->
    <div
      ref="terminalRef"
      class="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-y-auto font-mono text-xs text-zinc-300 space-y-1 selection:bg-zinc-800"
    >
      <div v-if="filteredLogs.length === 0" class="h-full flex flex-col items-center justify-center text-zinc-600">
        <AppIcon name="terminal" :size="20" class="mb-1.5 opacity-40" />
        <span v-if="wsStore.logs.length === 0">Listening for pipeline events...</span>
        <span v-else>No logs match filter</span>
      </div>

      <div
        v-for="log in filteredLogs"
        :key="log.id || log.timestamp"
        class="flex items-start space-x-2 leading-relaxed hover:bg-zinc-900/40 rounded px-1 -mx-1 transition-colors"
      >
        <!-- Timestamp -->
        <span class="text-zinc-600 shrink-0 select-none">
          {{ formatTime(log.timestamp) }}
        </span>

        <!-- Message -->
        <span class="break-all" :class="getLogStyle(log.level).text">
          {{ log.message }}
        </span>
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
