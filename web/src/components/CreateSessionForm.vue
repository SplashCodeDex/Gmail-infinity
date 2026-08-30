<template>
  <div class="surface-card p-6">
    <!-- Header -->
    <div class="flex items-center justify-between pb-4 mb-5 border-b border-zinc-800">
      <div class="flex items-center space-x-3">
        <div class="w-9 h-9 rounded-lg bg-indigo-950/60 border border-indigo-800/80 flex items-center justify-center text-indigo-400">
          <AppIcon name="plus" :size="18" />
        </div>
        <div>
          <h2 class="text-base font-bold text-zinc-100">Create Session</h2>
          <p class="text-xs text-zinc-400">Configure autonomous provisioning job</p>
        </div>
      </div>
      <span class="px-2.5 py-0.5 rounded-full text-xs font-mono bg-zinc-800 text-zinc-300 border border-zinc-700">
        v2.0
      </span>
    </div>

    <!-- Presets Selector -->
    <div class="mb-5">
      <label class="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
        Quick Presets
      </label>
      <div class="grid grid-cols-3 gap-2">
        <button
          v-for="preset in SESSION_PRESETS"
          :key="preset.id"
          type="button"
          @click="applyPreset(preset)"
          class="px-2.5 py-2 rounded-lg text-xs font-medium border text-center transition-all"
          :class="activePresetId === preset.id
            ? 'bg-indigo-600 text-white border-indigo-500 shadow-sm'
            : 'bg-zinc-950/80 text-zinc-300 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800/60'"
        >
          <div class="font-semibold">{{ preset.name }}</div>
        </button>
      </div>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <!-- Target Accounts & Concurrency Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <!-- Number of Accounts -->
        <div>
          <label class="block text-xs font-medium text-zinc-300 mb-1.5 flex items-center justify-between">
            <span>Target Accounts</span>
            <span class="font-mono text-zinc-500 text-[11px]">1 - 1,000</span>
          </label>
          <div class="relative">
            <input
              v-model.number="form.num_accounts"
              type="number"
              min="1"
              max="1000"
              class="form-input font-mono pr-8"
              required
            />
            <span class="absolute right-3 top-2.5 text-xs text-zinc-500 font-mono">qty</span>
          </div>
        </div>

        <!-- Concurrent Workers -->
        <div>
          <label class="block text-xs font-medium text-zinc-300 mb-1.5 flex items-center justify-between">
            <span>Worker Threads</span>
            <span class="font-mono text-zinc-500 text-[11px]">Parallel</span>
          </label>
          <select
            v-model.number="form.concurrent"
            class="form-input"
          >
            <option
              v-for="opt in WORKER_OPTIONS"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </div>
      </div>

      <!-- Engine Mode & Identity Name Pool Selection -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
        <!-- Automation Core Selector -->
        <div>
          <label class="block text-xs font-medium text-zinc-300 mb-1.5">
            Automation Driver Core
          </label>
          <select
            v-model="form.engine_mode"
            class="form-input"
          >
            <option
              v-for="eng in ENGINE_MODES"
              :key="eng.id"
              :value="eng.id"
            >
              {{ eng.label }}
            </option>
          </select>
        </div>

        <!-- Name / Identity Language -->
        <div>
          <label class="block text-xs font-medium text-zinc-300 mb-1.5">
            Identity Name Pool
          </label>
          <select
            v-model="form.use_arabic_names"
            class="form-input"
          >
            <option :value="false">Western / Standard (US/EU)</option>
            <option :value="true">Arabic / Middle Eastern</option>
          </select>
        </div>
      </div>

      <!-- Engine Toggles -->
      <div class="space-y-2.5 pt-2">
        <label class="block text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Engine Intelligence Modules
        </label>

        <ToggleSwitch
          v-model="form.use_proxies"
          label="Proxy Rotation & Routing"
          description="Rotate pool IPs per account request"
          icon="shield"
          color="indigo"
        />

        <ToggleSwitch
          v-model="form.warmup"
          label="Profile & Cookie Warming"
          description="Simulate realistic initial browsing activity"
          icon="flame"
          color="amber"
        />

        <ToggleSwitch
          v-model="form.adaptive"
          label="Adaptive Anti-Bot Engine"
          description="Humanized typing & dynamic delay jitter"
          icon="brain"
          color="indigo"
        />

        <ToggleSwitch
          v-model="form.use_sms"
          label="SMS Verification Gateway"
          description="Auto-purchase & verify disposable phone numbers"
          icon="smartphone"
          color="cyan"
        />
      </div>

      <!-- Advanced Stealth Modules Collapsible Section -->
      <div class="pt-2">
        <button
          type="button"
          @click="showAdvancedStealth = !showAdvancedStealth"
          class="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center space-x-1.5 transition"
        >
          <AppIcon name="sliders" :size="13" />
          <span>{{ showAdvancedStealth ? 'Hide Deep Stealth Controls' : 'Show Deep Stealth Controls' }}</span>
        </button>

        <div v-if="showAdvancedStealth" class="space-y-2.5 pt-3 mt-2 border-t border-zinc-800/80">
          <ToggleSwitch
            v-model="form.enable_poltergeist"
            label="Poltergeist PRNG Canvas/WebGL Noise"
            description="Inject unique session noise to avoid hardware clustering"
            icon="shield"
            color="indigo"
          />

          <ToggleSwitch
            v-model="form.enable_cookie_reaper"
            label="Cookie Reaper Pre-Trust Ingestion"
            description="Re-sign & inject HMAC-SHA1 session cookies before signup"
            icon="database"
            color="emerald"
          />

          <ToggleSwitch
            v-model="form.enable_recovery_chain"
            label="Daisy-Chain Recovery Linking"
            description="Automatically link created accounts as recovery emails"
            icon="users"
            color="cyan"
          />
        </div>
      </div>

      <!-- Export Format Selector -->
      <div class="pt-2">
        <label class="block text-xs font-medium text-zinc-300 mb-1.5">
          Automatic Export Format
        </label>
        <select
          v-model="form.export_format"
          class="form-input"
        >
          <option
            v-for="fmt in EXPORT_FORMATS"
            :key="fmt.value"
            :value="fmt.value"
          >
            {{ fmt.label }}
          </option>
        </select>
      </div>

      <!-- Submit Action Button (Zero Gradient, Solid High Contrast) -->
      <div class="pt-3">
        <button
          type="submit"
          :disabled="loading"
          class="btn-primary w-full py-3 text-sm font-semibold tracking-wide"
        >
          <AppIcon v-if="!loading" name="play" :size="16" class="mr-1.5" />
          <svg
            v-else
            class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
          </svg>
          <span>{{ loading ? 'Initializing Engine Pipeline...' : 'Launch Creation Session' }}</span>
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useAppStore } from '../stores/app'
import {
  WORKER_OPTIONS,
  EXPORT_FORMATS,
  SESSION_PRESETS,
  DEFAULT_SESSION_CONFIG,
  ENGINE_MODES,
} from '../constants/config'
import ToggleSwitch from './ToggleSwitch.vue'
import AppIcon from './AppIcon.vue'

const emit = defineEmits(['session-started'])
const app = useAppStore()

const loading = ref(false)
const activePresetId = ref('standard')
const showAdvancedStealth = ref(false)

const form = reactive({
  ...DEFAULT_SESSION_CONFIG,
})

function applyPreset(preset) {
  activePresetId.value = preset.id
  Object.assign(form, preset.config)
}

async function handleSubmit() {
  loading.value = true
  try {
    await app.startSession(form)
    emit('session-started')
  } catch (error) {
    console.error('Session start error:', error)
  } finally {
    loading.value = false
  }
}
</script>
