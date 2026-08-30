<template>
  <div class="surface-card p-6 space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-zinc-800 gap-3">
      <div class="flex items-center space-x-3">
        <div class="w-9 h-9 rounded-lg bg-indigo-950/60 border border-indigo-800/80 flex items-center justify-center text-indigo-400">
          <AppIcon name="cpu" :size="18" />
        </div>
        <div>
          <h2 class="text-base font-bold text-zinc-100">Engine Diagnostics & Service Hub</h2>
          <p class="text-xs text-zinc-400">Underlying automation infrastructure, SMS gateway credits, stealth matrix & alert integrations</p>
        </div>
      </div>
      <button
        @click="refreshAll"
        :disabled="isRefreshing"
        class="btn-secondary py-1.5 px-3 text-xs flex items-center space-x-1.5"
        title="Refresh system diagnostics and balances"
      >
        <AppIcon name="refresh-cw" :size="14" :class="isRefreshing ? 'animate-spin text-indigo-400' : ''" />
        <span>{{ isRefreshing ? 'Checking...' : 'Refresh All' }}</span>
      </button>
    </div>

    <!-- Diagnostic Grid (Solid Colors, Zero Gradient) -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- Card 1: Browser Automation Core -->
      <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800 space-y-3">
        <div class="text-xs font-semibold uppercase tracking-wider text-zinc-400 font-mono flex items-center justify-between">
          <span>Automation Runtime</span>
          <AppIcon name="server" :size="14" class="text-indigo-400" />
        </div>

        <div class="space-y-2 text-xs font-mono">
          <div class="flex items-center justify-between py-1 border-b border-zinc-900">
            <span class="text-zinc-400">Default Driver</span>
            <span class="text-indigo-400 font-bold uppercase">{{ config.engine || 'PLAYWRIGHT' }}</span>
          </div>

          <div class="flex items-center justify-between py-1 border-b border-zinc-900">
            <span class="text-zinc-400">Headless Execution</span>
            <span :class="config.headless ? 'text-cyan-400' : 'text-amber-400'">
              {{ config.headless ? 'Enabled (Background)' : 'Disabled (Visible)' }}
            </span>
          </div>

          <div class="flex items-center justify-between py-1">
            <span class="text-zinc-400">Master Password</span>
            <span :class="config.password_set ? 'text-emerald-400' : 'text-rose-400'">
              {{ config.password_set ? 'Configured & Active' : 'Not Set' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Card 2: Live SMS Gateways & Credits -->
      <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800 space-y-3">
        <div class="text-xs font-semibold uppercase tracking-wider text-zinc-400 font-mono flex items-center justify-between">
          <span>SMS Gateway Balances</span>
          <AppIcon name="smartphone" :size="14" class="text-cyan-400" />
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
                class="text-emerald-400 font-bold"
              >
                ${{ Number(smsBalances[provider]).toFixed(2) }}
              </span>
              <span
                class="px-2 py-0.5 rounded text-[10px] font-semibold"
                :class="isConfigured
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  : 'bg-zinc-800 text-zinc-500 border border-zinc-700'"
              >
                {{ isConfigured ? 'ONLINE' : 'UNSET' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Card 3: Telegram Alert Integration -->
      <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800 space-y-3 flex flex-col justify-between">
        <div>
          <div class="text-xs font-semibold uppercase tracking-wider text-zinc-400 font-mono flex items-center justify-between mb-3">
            <span>Telegram Bot Alerts</span>
            <AppIcon name="mail" :size="14" class="text-indigo-400" />
          </div>

          <div class="space-y-2 text-xs font-mono">
            <div class="flex items-center justify-between py-1 border-b border-zinc-900">
              <span class="text-zinc-400">Telegram Bot</span>
              <span
                class="px-2 py-0.5 rounded text-[10px] font-semibold"
                :class="capabilities?.telegram?.configured
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  : 'bg-zinc-800 text-zinc-500 border border-zinc-700'"
              >
                {{ capabilities?.telegram?.configured ? 'CONNECTED' : 'UNCONFIGURED' }}
              </span>
            </div>
            <p class="text-[11px] text-zinc-500 pt-1">
              Dispatches real-time HTML alerts for creation success, errors, and batch stats.
            </p>
          </div>
        </div>

        <button
          @click="handleTestTelegram"
          :disabled="isTestingTelegram"
          class="btn-secondary w-full py-1.5 text-xs mt-2"
        >
          <AppIcon name="zap" :size="13" class="text-indigo-400 mr-1.5" />
          <span>{{ isTestingTelegram ? 'Dispatching Test...' : 'Send Test Notification' }}</span>
        </button>
      </div>
    </div>

    <!-- Deep Anti-Detection & Stealth Matrix -->
    <div class="bg-zinc-950/80 p-5 rounded-xl border border-zinc-800 space-y-4">
      <div class="flex items-center justify-between border-b border-zinc-800/80 pb-3">
        <div class="flex items-center space-x-2.5">
          <AppIcon name="shield" :size="16" class="text-indigo-400" />
          <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-200 font-mono">
            Deep Stealth & Anti-Fingerprint Matrix
          </h3>
        </div>
        <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-950 text-indigo-300 border border-indigo-800">
          Hardware & Browser Emulation
        </span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs font-mono">
        <div class="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800/80 space-y-1">
          <div class="text-zinc-400 text-[11px]">Poltergeist PRNG Spoofing</div>
          <div class="flex items-center justify-between pt-0.5">
            <span class="text-zinc-200">Canvas / WebGL Noise</span>
            <span class="text-emerald-400 font-bold">ACTIVE</span>
          </div>
        </div>

        <div class="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800/80 space-y-1">
          <div class="text-zinc-400 text-[11px]">Cookie Reaper Ingestion</div>
          <div class="flex items-center justify-between pt-0.5">
            <span class="text-zinc-200">HMAC-SHA1 Pre-Trust</span>
            <span class="text-emerald-400 font-bold">READY</span>
          </div>
        </div>

        <div class="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800/80 space-y-1">
          <div class="text-zinc-400 text-[11px]">Ghost Typer Behavior</div>
          <div class="flex items-center justify-between pt-0.5">
            <span class="text-zinc-200">Bezier & Typo Jitter</span>
            <span class="text-emerald-400 font-bold">ENGAGED</span>
          </div>
        </div>

        <div class="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800/80 space-y-1">
          <div class="text-zinc-400 text-[11px]">Daisy-Chain Recovery</div>
          <div class="flex items-center justify-between pt-0.5">
            <span class="text-zinc-200">Account Hierarchies</span>
            <span class="text-emerald-400 font-bold">ENABLED</span>
          </div>
        </div>

        <div class="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800/80 space-y-1">
          <div class="text-zinc-400 text-[11px]">Android Appium Native OS</div>
          <div class="flex items-center justify-between pt-0.5">
            <span class="text-zinc-200">Emulator OS Settings</span>
            <span class="text-cyan-400 font-bold">AVAILABLE</span>
          </div>
        </div>

        <div class="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800/80 space-y-1">
          <div class="text-zinc-400 text-[11px]">MAC Address Rotation</div>
          <div class="flex items-center justify-between pt-0.5">
            <span class="text-zinc-200">NIC Hardware Masking</span>
            <span class="text-zinc-400 font-bold">OPTIONAL</span>
          </div>
        </div>
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
