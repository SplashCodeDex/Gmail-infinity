<template>
  <div class="surface-card p-5">
    <!-- Header -->
    <div class="flex items-center justify-between pb-3.5 mb-4 border-b border-zinc-800">
      <div class="flex items-center space-x-2.5">
        <div class="w-8 h-8 rounded-lg bg-emerald-950/60 border border-emerald-800/80 flex items-center justify-center text-emerald-400">
          <AppIcon name="activity" :size="16" />
        </div>
        <div>
          <h2 class="text-sm font-bold text-zinc-100">Job Pipeline</h2>
        </div>
      </div>
      <span class="px-2 py-0.5 rounded text-[11px] font-mono bg-zinc-800 text-zinc-300 border border-zinc-700">
        {{ sessions.length }} {{ sessions.length === 1 ? 'Job' : 'Jobs' }}
      </span>
    </div>

    <!-- Empty State -->
    <div
      v-if="!sessions || sessions.length === 0"
      class="text-center py-6 px-4 rounded-xl border border-dashed border-zinc-800/80 bg-zinc-950/30"
    >
      <AppIcon name="server" :size="20" class="mx-auto mb-2 text-zinc-600" />
      <p class="text-xs text-zinc-500">
        No active background workers. Launch a job to start creation.
      </p>
    </div>

    <!-- Sessions List -->
    <div v-else class="space-y-4">
      <div
        v-for="session in sessions"
        :key="session.id"
        class="bg-zinc-950/80 rounded-xl p-5 border border-zinc-800 hover:border-zinc-700/80 transition"
      >
        <!-- Top Row -->
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center space-x-3">
            <span
              class="w-2.5 h-2.5 rounded-full"
              :class="[
                getStatusIndicator(session.status),
                session.status === 'running' ? 'ping-indicator' : ''
              ]"
            ></span>
            <span class="font-mono text-xs font-semibold text-zinc-200 tracking-wide">{{ session.id }}</span>
          </div>
          <span
            class="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium uppercase"
            :class="getStatusBadgeClass(session.status)"
          >
            {{ session.status }}
          </span>
        </div>

        <!-- Progress Metrics -->
        <div class="mb-4">
          <div class="flex justify-between text-xs mb-1.5 font-mono">
            <span class="text-zinc-400">Batch Progress</span>
            <span class="text-zinc-200 font-semibold">
              {{ session.progress?.current || 0 }} / {{ session.progress?.total || 0 }} Accounts ({{ getProgressPercent(session) }}%)
            </span>
          </div>

          <!-- Solid Progress Bar (Zero Gradient) -->
          <div class="w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
            <div
              class="h-2 rounded-full transition-all duration-300"
              :class="session.status === 'failed' ? 'bg-rose-500' : 'bg-indigo-500'"
              :style="{ width: `${getProgressPercent(session)}%` }"
            ></div>
          </div>
        </div>

        <!-- Stats Breakdown Grid -->
        <div class="grid grid-cols-3 gap-2 text-xs mb-3">
          <div class="p-2.5 bg-zinc-900 border border-zinc-800/80 rounded-lg text-center">
            <div class="text-emerald-400 font-mono font-bold text-sm">{{ session.progress?.successes || 0 }}</div>
            <div class="text-zinc-500 text-[11px] uppercase tracking-wider">Success</div>
          </div>
          <div class="p-2.5 bg-zinc-900 border border-zinc-800/80 rounded-lg text-center">
            <div class="text-rose-400 font-mono font-bold text-sm">{{ session.progress?.failures || 0 }}</div>
            <div class="text-zinc-500 text-[11px] uppercase tracking-wider">Failed</div>
          </div>
          <div class="p-2.5 bg-zinc-900 border border-zinc-800/80 rounded-lg text-center">
            <div class="text-cyan-400 font-mono font-bold text-sm">
              {{ (session.progress?.success_rate || 0).toFixed(1) }}%
            </div>
            <div class="text-zinc-500 text-[11px] uppercase tracking-wider">Yield Rate</div>
          </div>
        </div>

        <!-- Actions -->
        <div v-if="session.status === 'running'" class="pt-1">
          <button
            @click="handleStop(session.id)"
            class="btn-danger w-full py-2 text-xs"
          >
            <AppIcon name="square" :size="14" class="mr-1.5" />
            <span>Terminate Session</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { SESSION_STATUS_STYLES } from '../constants/config'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  sessions: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['stop-session'])

function getProgressPercent(session) {
  if (!session?.progress?.total) return 0
  const pct = (session.progress.current / session.progress.total) * 100
  return Math.min(100, Math.max(0, Number(pct.toFixed(1))))
}

function getStatusIndicator(status) {
  return SESSION_STATUS_STYLES[status]?.indicator || 'bg-zinc-500'
}

function getStatusBadgeClass(status) {
  return SESSION_STATUS_STYLES[status]?.badge || 'bg-zinc-800 text-zinc-400 border-zinc-700'
}

function handleStop(sessionId) {
  emit('stop-session', sessionId)
}
</script>
