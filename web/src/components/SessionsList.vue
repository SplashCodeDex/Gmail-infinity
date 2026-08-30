<template>
  <div class="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-6">
    <h2 class="text-xl font-bold mb-4 flex items-center">
      <span class="mr-3">📋</span>
      Active Sessions
    </h2>

    <div v-if="!sessions || sessions.length === 0" class="text-center py-8">
      <p class="text-gray-400">No active sessions. Start one to begin!</p>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="session in sessions"
        :key="session.id"
        class="bg-gray-700 rounded-lg p-4 border border-gray-600"
      >
        <!-- Header -->
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center space-x-3">
            <div
              :class="[
                'w-3 h-3 rounded-full',
                getStatusColor(session.status),
                session.status === 'running' ? 'animate-pulse' : ''
              ]"
            ></div>
            <span class="font-mono text-sm text-gray-400">{{ session.id }}</span>
          </div>
          <span
            :class="[
              'px-3 py-1 rounded-full text-xs font-semibold uppercase',
              getStatusBadgeClass(session.status)
            ]"
          >
            {{ session.status }}
          </span>
        </div>

        <!-- Progress Bar -->
        <div class="mb-3">
          <div class="flex justify-between text-sm mb-1">
            <span class="text-gray-400">Progress</span>
            <span class="text-white font-semibold">
              {{ session.progress.current }}/{{ session.progress.total }}
            </span>
          </div>
          <div class="w-full bg-gray-600 rounded-full h-2">
            <div
              class="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all duration-500"
              :style="{ width: getProgressPercent(session) + '%' }"
            ></div>
          </div>
        </div>

        <!-- Stats Grid -->
        <div class="grid grid-cols-3 gap-2 text-xs">
          <div class="text-center p-2 bg-green-500/10 rounded">
            <div class="text-green-400 font-bold">{{ session.progress.successes }}</div>
            <div class="text-gray-400">Success</div>
          </div>
          <div class="text-center p-2 bg-red-500/10 rounded">
            <div class="text-red-400 font-bold">{{ session.progress.failures }}</div>
            <div class="text-gray-400">Failed</div>
          </div>
          <div class="text-center p-2 bg-blue-500/10 rounded">
            <div class="text-blue-400 font-bold">
              {{ session.progress.success_rate.toFixed(1) }}%
            </div>
            <div class="text-gray-400">Rate</div>
          </div>
        </div>

        <!-- Stop Button -->
        <button
          v-if="session.status === 'running'"
          @click="handleStop(session.id)"
          class="w-full mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-white text-sm transition flex items-center justify-center space-x-2"
        >
          <span>⏹️</span>
          <span>Stop Session</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  sessions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['stop-session'])

function getProgressPercent(session) {
  if (!session.progress.total) return 0
  return (session.progress.current / session.progress.total * 100).toFixed(1)
}

function getStatusColor(status) {
  const colors = {
    running: 'bg-green-500',
    completed: 'bg-blue-500',
    failed: 'bg-red-500',
    stopped: 'bg-yellow-500',
    initializing: 'bg-purple-500'
  }
  return colors[status] || 'bg-gray-500'
}

function getStatusBadgeClass(status) {
  const classes = {
    running: 'bg-green-500/20 text-green-400',
    completed: 'bg-blue-500/20 text-blue-400',
    failed: 'bg-red-500/20 text-red-400',
    stopped: 'bg-yellow-500/20 text-yellow-400',
    initializing: 'bg-purple-500/20 text-purple-400'
  }
  return classes[status] || 'bg-gray-500/20 text-gray-400'
}

function handleStop(sessionId) {
  if (confirm('Are you sure you want to stop this session?')) {
    emit('stop-session', sessionId)
  }
}
</script>
