<template>
  <div class="surface-card p-6">
    <!-- Header -->
    <div class="flex items-center space-x-3 pb-4 mb-4 border-b border-zinc-800">
      <div class="w-9 h-9 rounded-lg bg-indigo-950/60 border border-indigo-800/80 flex items-center justify-center text-indigo-400">
        <AppIcon name="zap" :size="18" />
      </div>
      <div>
        <h2 class="text-base font-bold text-zinc-100">Quick Controls</h2>
        <p class="text-xs text-zinc-400">Global utilities & batch operations</p>
      </div>
    </div>

    <div class="space-y-2.5">
      <!-- Test Proxies Button -->
      <button
        @click="handleTestProxies"
        :disabled="loading.proxies"
        class="w-full btn-secondary justify-start py-2.5"
      >
        <AppIcon v-if="!loading.proxies" name="shield" :size="16" class="text-indigo-400 mr-2" />
        <svg
          v-else
          class="animate-spin h-4 w-4 text-indigo-400 mr-2"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
        </svg>
        <span class="text-xs font-semibold">{{ loading.proxies ? 'Testing Latencies...' : 'Test All Proxies' }}</span>
      </button>

      <!-- View Accounts Database Button -->
      <button
        @click="$emit('switch-tab', 'accounts')"
        class="w-full btn-secondary justify-start py-2.5"
      >
        <AppIcon name="database" :size="16" class="text-emerald-400 mr-2" />
        <span class="text-xs font-semibold">Open Accounts Vault ({{ app.accounts.length }})</span>
      </button>

      <!-- Export JSON Button -->
      <button
        @click="handleExportAccounts"
        :disabled="loading.export"
        class="w-full btn-secondary justify-start py-2.5"
      >
        <AppIcon v-if="!loading.export" name="download" :size="16" class="text-cyan-400 mr-2" />
        <svg
          v-else
          class="animate-spin h-4 w-4 text-cyan-400 mr-2"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
        </svg>
        <span class="text-xs font-semibold">{{ loading.export ? 'Exporting Vault...' : 'Quick Export (JSON)' }}</span>
      </button>

      <!-- Refresh Dashboard Button -->
      <button
        @click="handleRefresh"
        :disabled="app.isRefreshing"
        class="w-full btn-secondary justify-start py-2.5"
      >
        <AppIcon
          name="refresh-cw"
          :size="16"
          class="text-zinc-400 mr-2"
          :class="app.isRefreshing ? 'animate-spin text-indigo-400' : ''"
        />
        <span class="text-xs font-semibold">{{ app.isRefreshing ? 'Refreshing Data...' : 'Sync Dashboard Data' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useAppStore } from '../stores/app'
import AppIcon from './AppIcon.vue'

const emit = defineEmits(['refresh', 'switch-tab'])
const app = useAppStore()

const loading = reactive({
  proxies: false,
  export: false,
})

async function handleTestProxies() {
  loading.proxies = true
  try {
    await app.testProxies()
  } catch (error) {
    console.error('Test proxies failed:', error)
  } finally {
    loading.proxies = false
  }
}

async function handleExportAccounts() {
  loading.export = true
  try {
    await app.exportAccounts('json')
  } catch (error) {
    console.error('Export accounts failed:', error)
  } finally {
    loading.export = false
  }
}

function handleRefresh() {
  emit('refresh')
}
</script>
