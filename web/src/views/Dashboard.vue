<template>
  <div class="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans selection:bg-indigo-600 selection:text-white">
    <!-- Solid Architectural Navigation Bar (Zero Gradient) -->
    <header class="bg-zinc-900 border-b border-zinc-800 sticky top-0 z-40 backdrop-blur-md bg-zinc-900/95">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <!-- Brand & Identity -->
          <div class="flex items-center space-x-3.5">
            <div class="w-10 h-10 rounded-xl bg-indigo-600 border border-indigo-500 flex items-center justify-center text-white shadow-sm shrink-0">
              <AppIcon name="mail" :size="22" strokeWidth="2.2" />
            </div>
            <div>
              <div class="flex items-center space-x-2">
                <span class="text-base font-bold text-zinc-100 tracking-tight">{{ APP_CONFIG.name }}</span>
                <span class="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-zinc-800 text-indigo-300 border border-zinc-700">
                  v{{ APP_CONFIG.version }}
                </span>
              </div>
              <p class="text-xs text-zinc-400 font-normal hidden sm:block">{{ APP_CONFIG.tagline }}</p>
            </div>
          </div>

          <!-- Live Status & Sync Header Controls -->
          <div class="flex items-center space-x-3">
            <!-- WebSocket Ping Status -->
            <div class="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-xs font-mono">
              <span
                class="w-2 h-2 rounded-full"
                :class="ws.connected ? 'bg-emerald-500 ping-indicator' : 'bg-rose-500'"
              ></span>
              <span :class="ws.connected ? 'text-emerald-400' : 'text-rose-400'">
                {{ ws.connected ? 'Pipeline Connected' : 'Pipeline Reconnecting' }}
              </span>
            </div>

            <!-- Global Refresh Action -->
            <button
              @click="refreshAll"
              :disabled="app.isRefreshing"
              class="btn-secondary py-1.5 px-3 text-xs"
              title="Sync state from FastAPI backend"
            >
              <AppIcon
                name="refresh-cw"
                :size="14"
                :class="app.isRefreshing ? 'animate-spin text-indigo-400' : ''"
              />
              <span class="hidden sm:inline">Sync</span>
            </button>
          </div>
        </div>

        <!-- Navigation Tabs Bar -->
        <div class="flex items-center space-x-1 border-t border-zinc-800/80 py-2 overflow-x-auto">
          <button
            v-for="tab in NAV_TABS"
            :key="tab.id"
            @click="currentTab = tab.id"
            class="px-3.5 py-1.5 rounded-lg text-xs font-medium transition flex items-center space-x-2 shrink-0"
            :class="currentTab === tab.id
              ? 'bg-zinc-800 text-zinc-100 font-semibold border border-zinc-700'
              : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent'"
          >
            <AppIcon :name="tab.icon" :size="14" />
            <span>{{ tab.label }}</span>
            <span
              v-if="tab.id === 'accounts' && app.accounts.length > 0"
              class="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-zinc-700 text-zinc-300"
            >
              {{ app.accounts.length }}
            </span>
          </button>
        </div>
      </div>
    </header>

    <!-- Main View Content Area -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <!-- High-Level Metric Stat Cards (Always visible on Overview, solid cards) -->
      <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Generated Accounts"
          :value="app.stats?.accounts?.total || 0"
          :subtitle="`${app.stats?.accounts?.successes || 0} Successful`"
          icon="users"
          variant="indigo"
        />
        <StatCard
          title="Creation Success Yield"
          :value="`${(app.stats?.accounts?.success_rate || 0).toFixed(1)}%`"
          subtitle="Batch Efficiency"
          icon="activity"
          variant="emerald"
        />
        <StatCard
          title="Operational Proxies"
          :value="`${app.stats?.proxies?.healthy || 0} / ${app.stats?.proxies?.total || 0}`"
          subtitle="Healthy Endpoints"
          icon="shield"
          variant="cyan"
        />
        <StatCard
          title="Active Sessions"
          :value="app.stats?.active_sessions || 0"
          :subtitle="ws.connected ? 'Pipeline Live' : 'Offline'"
          icon="zap"
          variant="amber"
        />
      </section>

      <!-- TAB 1: OVERVIEW -->
      <div v-if="currentTab === 'overview'" class="space-y-6">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <!-- Left Column (Session Launch & Controls) -->
          <div class="lg:col-span-5 space-y-6">
            <CreateSessionForm @session-started="handleSessionStarted" />
            <QuickActions @refresh="refreshAll" @switch-tab="currentTab = $event" />
          </div>

          <!-- Right Column (Live Sessions & Stream Logs) -->
          <div class="lg:col-span-7 space-y-6">
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

    <!-- Solid Minimalist Footer -->
    <footer class="bg-zinc-900 border-t border-zinc-800 py-6 mt-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-zinc-500 gap-3 font-mono">
        <div>
          <span>{{ APP_CONFIG.name }} © 2026 | Built by CodeDeX</span>
        </div>
        <div class="flex items-center space-x-4 text-zinc-400">
          <span>Vite + Vue 3</span>
          <span>•</span>
          <span>FastAPI Engine</span>
          <span>•</span>
          <span>Zero Gradient / SVG System</span>
        </div>
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
import QuickActions from '../components/QuickActions.vue'
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
