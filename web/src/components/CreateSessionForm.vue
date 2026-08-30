<template>
  <div class="surface-card p-5">
    <!-- Header -->
    <div class="flex items-center justify-between pb-3.5 mb-4 border-b border-zinc-800">
      <div class="flex items-center space-x-2.5">
        <div class="w-8 h-8 rounded-lg bg-indigo-950/60 border border-indigo-800/80 flex items-center justify-center text-indigo-400">
          <AppIcon name="play" :size="15" />
        </div>
        <div>
          <h2 class="text-sm font-bold text-zinc-100">Launch Session</h2>
        </div>
      </div>

      <!-- Presets Selector -->
      <div class="flex items-center space-x-1 bg-zinc-950 p-1 rounded-lg border border-zinc-800">
        <button
          v-for="preset in SESSION_PRESETS"
          :key="preset.id"
          type="button"
          @click="applyPreset(preset)"
          class="px-2 py-0.5 rounded text-[11px] font-medium transition"
          :class="activePresetId === preset.id
            ? 'bg-indigo-600 text-white font-semibold shadow-xs'
            : 'text-zinc-400 hover:text-zinc-200'"
        >
          {{ preset.name }}
        </button>
      </div>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-3.5">
      <!-- Target Accounts & Concurrency -->
      <div class="grid grid-cols-2 gap-3">
        <!-- Number of Accounts -->
        <div>
          <label class="block text-[11px] font-medium text-zinc-400 mb-1">
            Accounts
          </label>
          <div class="relative">
            <input
              v-model.number="form.num_accounts"
              type="number"
              min="1"
              max="1000"
              class="form-input font-mono text-xs py-1.5 pr-7"
              required
            />
            <span class="absolute right-2.5 top-1.5 text-[10px] text-zinc-500 font-mono">qty</span>
          </div>
        </div>

        <!-- Concurrent Workers -->
        <div>
          <label class="block text-[11px] font-medium text-zinc-400 mb-1">
            Workers
          </label>
          <select
            v-model.number="form.concurrent"
            class="form-input text-xs py-1.5"
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

      <!-- Feature Toggles Grid -->
      <div class="grid grid-cols-2 gap-2 pt-1">
        <button
          type="button"
          @click="form.use_proxies = !form.use_proxies"
          class="px-2.5 py-2 rounded-lg text-xs font-medium border flex items-center justify-between transition"
          :class="form.use_proxies
            ? 'bg-zinc-800/90 border-indigo-500/80 text-zinc-100'
            : 'bg-zinc-950/60 border-zinc-800 text-zinc-500'"
        >
          <div class="flex items-center space-x-1.5 truncate">
            <AppIcon name="shield" :size="13" :class="form.use_proxies ? 'text-indigo-400' : 'text-zinc-600'" />
            <span class="truncate">Proxy Routing</span>
          </div>
          <span class="w-1.5 h-1.5 rounded-full" :class="form.use_proxies ? 'bg-indigo-400' : 'bg-zinc-700'"></span>
        </button>

        <button
          type="button"
          @click="form.warmup = !form.warmup"
          class="px-2.5 py-2 rounded-lg text-xs font-medium border flex items-center justify-between transition"
          :class="form.warmup
            ? 'bg-zinc-800/90 border-amber-500/80 text-zinc-100'
            : 'bg-zinc-950/60 border-zinc-800 text-zinc-500'"
        >
          <div class="flex items-center space-x-1.5 truncate">
            <AppIcon name="flame" :size="13" :class="form.warmup ? 'text-amber-400' : 'text-zinc-600'" />
            <span class="truncate">Trust Warmup</span>
          </div>
          <span class="w-1.5 h-1.5 rounded-full" :class="form.warmup ? 'bg-amber-400' : 'bg-zinc-700'"></span>
        </button>

        <button
          type="button"
          @click="form.adaptive = !form.adaptive"
          class="px-2.5 py-2 rounded-lg text-xs font-medium border flex items-center justify-between transition"
          :class="form.adaptive
            ? 'bg-zinc-800/90 border-emerald-500/80 text-zinc-100'
            : 'bg-zinc-950/60 border-zinc-800 text-zinc-500'"
        >
          <div class="flex items-center space-x-1.5 truncate">
            <AppIcon name="brain" :size="13" :class="form.adaptive ? 'text-emerald-400' : 'text-zinc-600'" />
            <span class="truncate">Adaptive AI</span>
          </div>
          <span class="w-1.5 h-1.5 rounded-full" :class="form.adaptive ? 'bg-emerald-400' : 'bg-zinc-700'"></span>
        </button>

        <button
          type="button"
          @click="form.use_sms = !form.use_sms"
          class="px-2.5 py-2 rounded-lg text-xs font-medium border flex items-center justify-between transition"
          :class="form.use_sms
            ? 'bg-zinc-800/90 border-cyan-500/80 text-zinc-100'
            : 'bg-zinc-950/60 border-zinc-800 text-zinc-500'"
        >
          <div class="flex items-center space-x-1.5 truncate">
            <AppIcon name="smartphone" :size="13" :class="form.use_sms ? 'text-cyan-400' : 'text-zinc-600'" />
            <span class="truncate">SMS Gateway</span>
          </div>
          <span class="w-1.5 h-1.5 rounded-full" :class="form.use_sms ? 'bg-cyan-400' : 'bg-zinc-700'"></span>
        </button>
      </div>

      <!-- Export Format Row -->
      <div>
        <label class="block text-[11px] font-medium text-zinc-400 mb-1">
          Export Format
        </label>
        <select
          v-model="form.export_format"
          class="form-input text-xs py-1.5"
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

      <!-- Launch Button -->
      <div class="pt-1">
        <button
          type="submit"
          :disabled="loading"
          class="btn-primary w-full py-2 text-xs font-semibold"
        >
          <AppIcon v-if="!loading" name="play" :size="14" class="mr-1.5" />
          <svg
            v-else
            class="animate-spin -ml-1 mr-2 h-3.5 w-3.5 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
          </svg>
          <span>{{ loading ? 'Starting Engine...' : 'Start Creation Job' }}</span>
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
} from '../constants/config'
import AppIcon from './AppIcon.vue'

const emit = defineEmits(['session-started'])
const app = useAppStore()

const loading = ref(false)
const activePresetId = ref('standard')

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
