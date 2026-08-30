<!-- Quick Actions Panel -->
<template>
  <div class="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-6 mt-6">
    <h2 class="text-xl font-bold mb-4 flex items-center text-white">
      <span class="mr-3">⚡</span>
      Quick Actions
    </h2>
    <div class="space-y-3">
      <button
        @click="handleTestProxies"
        :disabled="loading.proxies"
        class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed rounded-lg text-white font-medium transition flex items-center justify-center space-x-2 shadow"
      >
        <span v-if="!loading.proxies">🧪</span>
        <span v-else class="animate-spin">⚙️</span>
        <span>{{ loading.proxies ? 'Testing Latency...' : 'Test All Proxies' }}</span>
      </button>

      <button
        @click="handleViewAccounts"
        class="w-full px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded-lg text-white font-medium transition flex items-center justify-center space-x-2 shadow"
      >
        <span>📋</span>
        <span>View Accounts ({{ app.accounts.length }})</span>
      </button>

      <button
        @click="handleExportAccounts"
        :disabled="loading.export"
        class="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 disabled:cursor-not-allowed rounded-lg text-white font-medium transition flex items-center justify-center space-x-2 shadow"
      >
        <span v-if="!loading.export">💾</span>
        <span v-else class="animate-spin">⚙️</span>
        <span>{{ loading.export ? 'Exporting...' : 'Export JSON' }}</span>
      </button>

      <button
        @click="handleRefresh"
        class="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white font-medium transition flex items-center justify-center space-x-2 shadow"
      >
        <span>🔄</span>
        <span>Refresh Dashboard</span>
      </button>
    </div>

    <!-- Proxy Test Results Modal -->
    <div v-if="modals.proxyResults" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div class="bg-gray-800 border border-gray-700 rounded-2xl max-w-lg w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        <div class="p-5 border-b border-gray-700 flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <span class="text-xl">🧪</span>
            <h3 class="text-lg font-bold text-white">Proxy Health Test Results</h3>
          </div>
          <button @click="modals.proxyResults = false" class="text-gray-400 hover:text-white text-xl">✕</button>
        </div>

        <div class="p-5 overflow-y-auto space-y-4 flex-1">
          <div class="grid grid-cols-3 gap-3 text-center">
            <div class="bg-gray-900/60 p-3 rounded-xl border border-gray-700">
              <div class="text-xs text-gray-400">Total Tested</div>
              <div class="text-xl font-bold text-white">{{ proxyData.total || 0 }}</div>
            </div>
            <div class="bg-gray-900/60 p-3 rounded-xl border border-emerald-900/50">
              <div class="text-xs text-emerald-400">Healthy</div>
              <div class="text-xl font-bold text-emerald-400">{{ proxyData.healthy || 0 }}</div>
            </div>
            <div class="bg-gray-900/60 p-3 rounded-xl border border-rose-900/50">
              <div class="text-xs text-rose-400">Unhealthy</div>
              <div class="text-xl font-bold text-rose-400">{{ proxyData.unhealthy || 0 }}</div>
            </div>
          </div>

          <div class="space-y-2">
            <div
              v-for="(p, i) in proxyData.proxies"
              :key="i"
              class="bg-gray-900/50 border border-gray-700/60 rounded-xl p-3 flex items-center justify-between text-sm"
            >
              <div class="font-mono text-gray-200 truncate mr-2">{{ p.proxy }}</div>
              <div class="flex items-center space-x-2 flex-shrink-0">
                <span
                  v-if="p.healthy"
                  class="px-2 py-0.5 text-xs font-bold rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800"
                >
                  {{ p.latency_ms }} ms
                </span>
                <span
                  v-else
                  class="px-2 py-0.5 text-xs font-bold rounded-full bg-rose-950 text-rose-300 border border-rose-800"
                >
                  Offline
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="p-4 border-t border-gray-700 bg-gray-800/80 flex justify-end">
          <button
            @click="modals.proxyResults = false"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium"
          >
            Done
          </button>
        </div>
      </div>
    </div>

    <!-- Accounts Viewer Modal -->
    <div v-if="modals.accounts" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div class="bg-gray-800 border border-gray-700 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        <div class="p-5 border-b border-gray-700 flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <span class="text-xl">📋</span>
            <h3 class="text-lg font-bold text-white">Registered Accounts ({{ app.accounts.length }})</h3>
          </div>
          <button @click="modals.accounts = false" class="text-gray-400 hover:text-white text-xl">✕</button>
        </div>

        <div class="p-5 overflow-y-auto space-y-3 flex-1">
          <div v-if="app.accounts.length === 0" class="text-center py-8 text-gray-400">
            No accounts created yet. Start a session to generate accounts!
          </div>
          <div
            v-for="(acc, i) in app.accounts"
            :key="i"
            class="bg-gray-900/60 border border-gray-700 rounded-xl p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
          >
            <div>
              <div class="font-bold text-white">{{ acc.email || acc.username }}</div>
              <div class="text-xs text-gray-400">Pass: {{ acc.password }}</div>
              <div v-if="acc.recovery_email" class="text-xs text-gray-500">Recovery: {{ acc.recovery_email }}</div>
            </div>
            <div class="text-xs text-purple-300 font-mono">
              {{ acc.created_at || 'Saved' }}
            </div>
          </div>
        </div>

        <div class="p-4 border-t border-gray-700 bg-gray-800/80 flex justify-between items-center">
          <button
            @click="handleExportAccounts"
            class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium"
          >
            Export All
          </button>
          <button
            @click="modals.accounts = false"
            class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useAppStore } from '../stores/app'

const emit = defineEmits(['refresh'])
const app = useAppStore()

const loading = reactive({
  proxies: false,
  export: false
})

const modals = reactive({
  proxyResults: false,
  accounts: false
})

const proxyData = reactive({
  total: 0,
  healthy: 0,
  unhealthy: 0,
  proxies: []
})

async function handleTestProxies() {
  loading.proxies = true
  try {
    const results = await app.testProxies()
    if (results) {
      proxyData.total = results.total || 0
      proxyData.healthy = results.healthy || 0
      proxyData.unhealthy = results.unhealthy || 0
      proxyData.proxies = results.proxies || []
      modals.proxyResults = true
    }
  } catch (error) {
    alert('Failed to test proxies: ' + error.message)
  } finally {
    loading.proxies = false
  }
}

async function handleViewAccounts() {
  try {
    await app.fetchAccounts()
    modals.accounts = true
  } catch (error) {
    alert('Failed to fetch accounts: ' + error.message)
  }
}

async function handleExportAccounts() {
  loading.export = true
  try {
    await app.exportAccounts('json')
  } catch (error) {
    alert('Failed to export accounts: ' + error.message)
  } finally {
    loading.export = false
  }
}

function handleRefresh() {
  emit('refresh')
}
</script>
