<template>
  <div class="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans selection:bg-indigo-600 selection:text-white">
    <!-- Slim Unified Top Navigation Bar -->
    <header class="bg-zinc-900/90 border-b border-zinc-800/80 sticky top-0 z-40 backdrop-blur-md">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-14">
          <!-- Left: Brand -->
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 rounded-lg bg-indigo-600 border border-indigo-500 flex items-center justify-center text-white shrink-0">
              <AppIcon name="mail" :size="17" strokeWidth="2.2" />
            </div>
            <span class="text-sm font-bold text-zinc-100 tracking-tight">{{ APP_CONFIG.name }}</span>
          </div>

          <!-- Center: Segment View Switcher -->
          <nav class="flex items-center space-x-1 bg-zinc-950/80 p-1 rounded-xl border border-zinc-800">
            <button
              v-for="tab in NAV_TABS"
              :key="tab.id"
              @click="currentTab = tab.id"
              class="px-3 py-1 rounded-lg text-xs font-medium transition flex items-center space-x-1.5"
              :class="currentTab === tab.id
                ? 'bg-zinc-800 text-zinc-100 font-semibold shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200'"
            >
              <AppIcon :name="tab.icon" :size="13" />
              <span>{{ tab.label }}</span>
            </button>
          </nav>

          <!-- Right: Sync Button -->
          <div class="flex items-center space-x-2">
            <button
              @click="refreshAll"
              :disabled="app.isRefreshing"
              class="btn-secondary py-1 px-2.5 text-xs flex items-center space-x-1.5"
              title="Sync state from FastAPI backend"
            >
              <AppIcon
                name="refresh-cw"
                :size="13"
                :class="app.isRefreshing ? 'animate-spin text-indigo-400' : ''"
              />
              <span class="hidden sm:inline text-xs">Sync</span>
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main View Area -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-5 space-y-5">
      <!-- High-Level Metric Stat Cards (Always visible on Overview) -->
      <section v-if="currentTab === 'overview'" class="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          title="Total Accounts"
          :value="app.stats?.accounts?.total || 0"
          :subtitle="`${app.stats?.accounts?.successes || 0} Successful`"
          icon="users"
          variant="indigo"
        />
        <StatCard
          title="Success Yield"
          :value="`${(app.stats?.accounts?.success_rate || 0).toFixed(1)}%`"
          subtitle="Batch Efficiency"
          icon="activity"
          variant="emerald"
        />
        <StatCard
          title="Active Proxies"
          :value="`${app.stats?.proxies?.healthy || 0} / ${app.stats?.proxies?.total || 0}`"
          subtitle="Healthy Pool"
          icon="shield"
          variant="cyan"
        />
        <StatCard
          title="Active Jobs"
          :value="app.stats?.active_sessions || 0"
          :subtitle="ws.connected ? 'Pipeline Live' : 'Offline'"
          icon="zap"
          variant="amber"
        />
      </section>

      <!-- TAB 1: OVERVIEW -->
      <div v-if="currentTab === 'overview'" class="space-y-5">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <!-- Left Column (Session Creator) -->
          <div class="lg:col-span-4 space-y-5">
            <CreateSessionForm @session-started="handleSessionStarted" />
          </div>

          <!-- Right Column (Active Sessions & Live Logs) -->
          <div class="lg:col-span-8 space-y-5">
            <SessionsList :sessions="app.sessions" @stop-session="stopSession" />
            <LogsPanel />
          </div>
        </div>
      </div>

      <!-- TAB 2: ACCOUNTS VAULT -->
      <div v-else-if="currentTab === 'accounts'">
        <AccountsTable />
      </div>

      <!-- TAB 3: PROXY NETWORK -->
      <div v-else-if="currentTab === 'proxies'">
        <ProxyMonitor />
      </div>

      <!-- TAB 4: LIVE TERMINAL -->
      <div v-else-if="currentTab === 'terminal'">
        <LogsPanel />
      </div>

      <!-- TAB 5: ENGINE DIAGNOSTICS -->
      <div v-else-if="currentTab === 'diagnostics'">
        <SystemDiagnostics />
      </div>
    </main>

    <!-- Minimalist Footer -->
    <footer class="bg-zinc-900/60 border-t border-zinc-800/80 py-4 mt-auto">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between text-xs text-zinc-500 font-mono">
        <div>{{ APP_CONFIG.name }} v{{ APP_CONFIG.version }}</div>
        <div class="text-zinc-500">{{ APP_CONFIG.tagline }}</div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '../stores/app'
import { useWebSocketStore } from '../stores/websocket'
import { NAV_TABS, APP_CONFIG } from '../constants/config'
import StatCard from '../components/StatCard.vue'
import CreateSessionForm from '../components/CreateSessionForm.vue'
import SessionsList from '../components/SessionsList.vue'
import LogsPanel from '../components/LogsPanel.vue'
import AccountsTable from '../components/AccountsTable.vue'
import ProxyMonitor from '../components/ProxyMonitor.vue'
import SystemDiagnostics from '../components/SystemDiagnostics.vue'
import AppIcon from '../components/AppIcon.vue'

const app = useAppStore()
const ws = useWebSocketStore()

const currentTab = ref('overview')
let refreshInterval = null

onMounted(async () => {
  ws.connect()
  await refreshAll()

  refreshInterval = setInterval(() => {
    refreshAll()
  }, APP_CONFIG.refreshIntervalMs)
})

onUnmounted(() => {
  ws.disconnect()
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

async function refreshAll() {
  await app.refreshAll()
}

function handleSessionStarted() {
  refreshAll()
}

async function stopSession(sessionId) {
  try {
    await app.stopSession(sessionId)
  } catch (error) {
    console.error('Stop session failed:', error)
  }
}
</script>
