<template>
  <div class="min-h-screen bg-gray-900">
    <!-- Header -->
    <nav class="gradient-bg shadow-lg">
      <div class="container mx-auto px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <div class="text-3xl">✉️</div>
            <div>
              <h1 class="text-2xl font-bold text-white">Gmail Infinity Factory</h1>
              <p class="text-purple-200 text-sm">Vite + Vue 3 + FastAPI Dashboard</p>
            </div>
          </div>
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div :class="['w-3 h-3 rounded-full', ws.connected ? 'bg-green-500 animate-pulse' : 'bg-red-500']"></div>
              <span class="text-sm text-white">{{ ws.connected ? 'Connected' : 'Disconnected' }}</span>
            </div>
            <button @click="refreshAll" class="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-white transition">
              🔄 Refresh
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Stats Cards -->
    <div class="container mx-auto px-6 py-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Accounts"
          :value="app.stats?.accounts?.total || 0"
          icon="👥"
          color="blue"
        />
        <StatCard
          title="Success Rate"
          :value="`${(app.stats?.accounts?.success_rate || 0).toFixed(1)}%`"
          icon="✅"
          color="green"
        />
        <StatCard
          title="Active Proxies"
          :value="app.stats?.proxies?.healthy || 0"
          icon="🛡️"
          color="purple"
        />
        <StatCard
          title="Active Sessions"
          :value="app.stats?.active_sessions || 0"
          icon="⚡"
          color="yellow"
        />
      </div>

      <!-- Main Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Left Column -->
        <div class="lg:col-span-1 space-y-6">
          <CreateSessionForm @session-started="handleSessionStarted" />
          <QuickActions @refresh="refreshAll" />
        </div>

        <!-- Right Column -->
        <div class="lg:col-span-2 space-y-6">
          <SessionsList :sessions="app.sessions" @stop-session="stopSession" />
          <LogsPanel :logs="ws.logs" />
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="bg-gray-800 border-t border-gray-700 mt-12 py-6">
      <div class="container mx-auto px-6 text-center text-gray-400">
        <p>Gmail Infinity Factory © 2026 | Enhanced Intelligence Engine | Built with Vite + Vue 3 + FastAPI</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useAppStore } from '../stores/app'
import { useWebSocketStore } from '../stores/websocket'
import StatCard from '../components/StatCard.vue'
import CreateSessionForm from '../components/CreateSessionForm.vue'
import SessionsList from '../components/SessionsList.vue'
import LogsPanel from '../components/LogsPanel.vue'
import QuickActions from '../components/QuickActions.vue'

const app = useAppStore()
const ws = useWebSocketStore()

let refreshInterval = null

onMounted(async () => {
  ws.connect()
  await refreshAll()

  // Auto-refresh every 5 seconds
  refreshInterval = setInterval(refreshAll, 5000)
})

onUnmounted(() => {
  ws.disconnect()
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

async function refreshAll() {
  try {
    await Promise.all([
      app.fetchStats(),
      app.fetchConfig(),
      app.fetchSessions()
    ])
  } catch (error) {
    console.error('Failed to refresh:', error)
  }
}

function handleSessionStarted() {
  refreshAll()
}

async function stopSession(sessionId) {
  try {
    await app.stopSession(sessionId)
  } catch (error) {
    console.error('Failed to stop session:', error)
    alert('Failed to stop session: ' + error.message)
  }
}
</script>
