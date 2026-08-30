<template>
  <div class="surface-card p-5 space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between pb-3.5 border-b border-zinc-800">
      <div class="flex items-center space-x-2.5">
        <div class="w-7 h-7 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-300">
          <AppIcon name="play" :size="14" />
        </div>
        <h2 class="text-sm font-semibold text-zinc-100">Launch Session</h2>
      </div>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-3.5">
      <!-- Registration Flow Route Selector -->
      <div>
        <label class="block text-[11px] font-medium text-zinc-400 mb-1.5">
          Registration Route
        </label>

        <div class="grid grid-cols-2 gap-1.5">
          <button
            v-for="flow in CREATION_FLOWS"
            :key="flow.id"
            type="button"
            @click="selectFlow(flow.id)"
            class="p-2 rounded-lg text-left border transition flex flex-col justify-between"
            :class="form.flow_mode === flow.id
              ? 'bg-zinc-800 border-zinc-700 text-zinc-100'
              : 'bg-zinc-950/50 border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700'"
          >
            <div class="flex items-center space-x-1.5 mb-1">
              <AppIcon
                :name="getFlowIcon(flow.id)"
                :size="13"
                :class="form.flow_mode === flow.id ? 'text-indigo-400' : 'text-zinc-500'"
              />
              <span class="text-xs font-medium truncate">{{ flow.name }}</span>
            </div>
            <span class="text-[10px] text-zinc-500 line-clamp-1 leading-tight">{{ flow.description }}</span>
          </button>
        </div>
      </div>

      <!-- Target Accounts & Concurrency -->
      <div class="grid grid-cols-2 gap-3">
        <!-- Number of Accounts -->
        <div>
          <label class="block text-[11px] font-medium text-zinc-400 mb-1">
            Accounts
          </label>
          <input
            v-model.number="form.num_accounts"
            type="number"
            min="1"
            max="1000"
            class="form-input font-mono text-xs py-1.5"
            required
          />
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
      <div class="grid grid-cols-4 gap-1.5 pt-0.5">
        <button
          type="button"
          @click="form.use_proxies = !form.use_proxies"
          class="px-2 py-1.5 rounded-lg text-xs font-medium border flex items-center justify-center space-x-1.5 transition"
          :class="form.use_proxies
            ? 'bg-zinc-800 border-zinc-700 text-zinc-100'
            : 'bg-zinc-950/60 border-zinc-800 text-zinc-500 hover:text-zinc-300'"
          title="Route browser requests through proxy pool"
        >
          <AppIcon name="shield" :size="13" />
          <span class="truncate">Proxies</span>
        </button>

        <button
          type="button"
          @click="form.warmup = !form.warmup"
          class="px-2 py-1.5 rounded-lg text-xs font-medium border flex items-center justify-center space-x-1.5 transition"
          :class="form.warmup
            ? 'bg-zinc-800 border-zinc-700 text-zinc-100'
            : 'bg-zinc-950/60 border-zinc-800 text-zinc-500 hover:text-zinc-300'"
          title="Build Google trust cookies before sign-up"
        >
          <AppIcon name="flame" :size="13" />
          <span class="truncate">Warmup</span>
        </button>

        <button
          type="button"
          @click="form.use_sms = !form.use_sms"
          class="px-2 py-1.5 rounded-lg text-xs font-medium border flex items-center justify-center space-x-1.5 transition"
          :class="form.use_sms
            ? 'bg-zinc-800 border-zinc-700 text-zinc-100'
            : 'bg-zinc-950/60 border-zinc-800 text-zinc-500 hover:text-zinc-300'"
          title="Use SMS API provider when phone verification is triggered"
        >
          <AppIcon name="smartphone" :size="13" />
          <span class="truncate">SMS</span>
        </button>

        <button
          type="button"
          @click="form.headless = !form.headless"
          class="px-2 py-1.5 rounded-lg text-xs font-medium border flex items-center justify-center space-x-1.5 transition"
          :class="!form.headless
            ? 'bg-zinc-800 border-zinc-700 text-indigo-400 font-semibold'
            : 'bg-zinc-950/60 border-zinc-800 text-zinc-500 hover:text-zinc-300'"
          :title="!form.headless ? 'Visible Browser UI: Window opens live on desktop' : 'Headless Browser: Runs in background'"
        >
          <AppIcon name="eye" :size="13" />
          <span class="truncate">{{ !form.headless ? 'Live UI' : 'Headless' }}</span>
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
          <span>{{ loading ? 'Starting...' : 'Start Creation Job' }}</span>
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
  CREATION_FLOWS,
  DEFAULT_SESSION_CONFIG,
} from '../constants/config'
import AppIcon from './AppIcon.vue'

const emit = defineEmits(['session-started'])
const app = useAppStore()

const loading = ref(false)

const form = reactive({
  ...DEFAULT_SESSION_CONFIG,
})

function selectFlow(flowId) {
  form.flow_mode = flowId
  form.adaptive = (flowId === 'adaptive')
}

function getFlowIcon(flowId) {
  switch (flowId) {
    case 'adaptive': return 'brain'
    case 'standard': return 'globe'
    case 'youtube': return 'play'
    case 'workspace': return 'server'
    default: return 'activity'
  }
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
