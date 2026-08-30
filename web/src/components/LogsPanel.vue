<template>
  <div class="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-6">
    <h2 class="text-xl font-bold mb-4 flex items-center justify-between">
      <span class="flex items-center">
        <span class="mr-3">💻</span>
        Live Logs
      </span>
      <button
        @click="clearLogs"
        class="text-xs px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded transition"
      >
        Clear
      </button>
    </h2>

    <div
      ref="logsContainer"
      class="bg-gray-900 rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm"
    >
      <div v-if="!logs || logs.length === 0" class="text-gray-500">
        Waiting for activity...
      </div>

      <div v-else>
        <div
          v-for="(log, index) in logs"
          :key="index"
          class="mb-2 flex items-start space-x-2"
        >
          <span class="text-gray-500 flex-shrink-0">
            [{{ formatTime(log.timestamp) }}]
          </span>
          <span :class="['flex-shrink-0', getLogIcon(log.level)]">
            {{ getLogEmoji(log.level) }}
          </span>
          <span :class="getLogColor(log.level)">
            {{ log.message }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  logs: {
    type: Array,
    default: () => []
  }
})

const logsContainer = ref(null)

// Auto-scroll to bottom when new logs arrive
watch(() => props.logs, async () => {
  await nextTick()
  if (logsContainer.value) {
    logsContainer.value.scrollTop = logsContainer.value.scrollHeight
  }
}, { deep: true })

function formatTime(timestamp) {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return '00:00:00'
  }
}

function getLogEmoji(level) {
  const emojis = {
    info: 'ℹ️',
    success: '✅',
    warning: '⚠️',
    error: '❌'
  }
  return emojis[level] || 'ℹ️'
}

function getLogIcon(level) {
  const colors = {
    info: 'text-blue-400',
    success: 'text-green-400',
    warning: 'text-yellow-400',
    error: 'text-red-400'
  }
  return colors[level] || 'text-gray-400'
}

function getLogColor(level) {
  const colors = {
    info: 'text-blue-400',
    success: 'text-green-400',
    warning: 'text-yellow-400',
    error: 'text-red-400'
  }
  return colors[level] || 'text-gray-400'
}

function clearLogs() {
  // Emit event to parent to clear logs
  // For now, this is just a placeholder
  console.log('Clear logs requested')
}
</script>
