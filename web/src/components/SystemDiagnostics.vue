<template>
  <div class="surface-card p-6 space-y-4">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-zinc-800 gap-3">
      <div class="flex items-center space-x-2.5">
        <div class="w-7 h-7 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-300">
          <AppIcon name="cpu" :size="14" />
        </div>
        <h2 class="text-sm font-semibold text-zinc-100">System Diagnostics</h2>
      </div>
      <button
        @click="refreshAll"
        :disabled="isRefreshing"
        class="btn-secondary py-1.5 px-3 text-xs flex items-center space-x-1.5"
        title="Refresh diagnostics"
      >
        <AppIcon name="refresh-cw" :size="13" :class="isRefreshing ? 'animate-spin text-indigo-400' : ''" />
        <span>{{ isRefreshing ? 'Checking...' : 'Refresh' }}</span>
      </button>
    </div>

    <!-- Diagnostic Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- Card 1: Browser Automation Core -->
      <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800 space-y-3">
        <div class="text-xs font-semibold text-zinc-400 font-mono flex items-center justify-between">
          <span>Runtime</span>
          <AppIcon name="server" :size="13" class="text-zinc-500" />
        </div>

        <div class="space-y-2 text-xs font-mono">
          <div class="flex items-center justify-between py-1 border-b border-zinc-900">
            <span class="text-zinc-400">Driver</span>
            <span class="text-zinc-200 font-semibold uppercase">{{ config.engine || 'PLAYWRIGHT' }}</span>
          </div>

          <div class="flex items-center justify-between py-1 border-b border-zinc-900">
            <span class="text-zinc-400">Headless</span>
            <span :class="config.headless ? 'text-zinc-200' : 'text-amber-400'">
              {{ config.headless ? 'Enabled' : 'Disabled' }}
            </span>
          </div>

          <div class="flex items-center justify-between py-1">
            <span class="text-zinc-400">Master Password</span>
            <span :class="config.password_set ? 'text-emerald-400' : 'text-zinc-500'">
              {{ config.password_set ? 'Active' : 'Unset' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Card 2: Live SMS Gateways & Credits -->
      <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800 space-y-3">
        <div class="text-xs font-semibold text-zinc-400 font-mono flex items-center justify-between">
          <span>SMS Gateways</span>
          <AppIcon name="smartphone" :size="13" class="text-zinc-500" />
        </div>

        <div class="space-y-2 text-xs font-mono">
          <div
            v-for="(isConfigured, provider) in (config.sms_providers || {})"
            :key="provider"
            class="flex items-center justify-between py-1 border-b border-zinc-900 last:border-0"
          >
            <span class="text-zinc-300 capitalize">{{ provider }}</span>
            <div class="flex items-center space-x-2">
              <span
                v-if="smsBalances[provider] !== undefined && smsBalances[provider] !== null"
                class="text-emerald-400 font-semibold"
              >
                ${{ Number(smsBalances[provider]).toFixed(2) }}
              </span>
              <span
                class="text-[11px] font-mono"
                :class="isConfigured ? 'text-emerald-400' : 'text-zinc-500'"
              >
                {{ isConfigured ? 'Active' : 'Unset' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Card 3: Telegram Alert Integration -->
      <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800 space-y-3 flex flex-col justify-between">
        <div>
          <div class="text-xs font-semibold text-zinc-400 font-mono flex items-center justify-between mb-3">
            <span>Telegram Alerts</span>
            <AppIcon name="mail" :size="13" class="text-zinc-500" />
          </div>

          <div class="space-y-2 text-xs font-mono">
            <div class="flex items-center justify-between py-1 border-b border-zinc-900">
              <span class="text-zinc-400">Status</span>
              <span
                class="text-[11px] font-mono"
                :class="capabilities?.telegram?.configured ? 'text-emerald-400' : 'text-zinc-500'"
              >
                {{ capabilities?.telegram?.configured ? 'Connected' : 'Unset' }}
              </span>
            </div>
          </div>
        </div>

        <button
          @click="handleTestTelegram"
          :disabled="isTestingTelegram"
          class="btn-secondary w-full py-1.5 text-xs mt-2"
        >
          <AppIcon name="zap" :size="13" class="mr-1.5 text-zinc-400" />
          <span>{{ isTestingTelegram ? 'Testing...' : 'Send Test Alert' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '../stores/app'
import AppIcon from './AppIcon.vue'

const appStore = useAppStore()
const config = computed(() => appStore.config || {})

const isRefreshing = ref(false)
const isTestingTelegram = ref(false)
const smsBalances = ref({})
const capabilities = ref(null)

onMounted(async () => {
  await refreshAll()
})

async function refreshAll() {
  isRefreshing.value = true
  try {
    await appStore.fetchConfig()
    const [balances, caps] = await Promise.allSettled([
      appStore.fetchSmsBalances(),
      appStore.fetchEngineCapabilities(),
    ])
    if (balances.status === 'fulfilled') smsBalances.value = balances.value || {}
    if (caps.status === 'fulfilled') capabilities.value = caps.value || null
  } finally {
    isRefreshing.value = false
  }
}

async function handleTestTelegram() {
  isTestingTelegram.value = true
  try {
    await appStore.testTelegram()
  } finally {
    isTestingTelegram.value = false
  }
}
</script>
