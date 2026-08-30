<template>
  <div class="surface-card p-5 space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between pb-3.5 border-b border-zinc-800">
      <div class="flex items-center space-x-2.5">
        <div class="w-7 h-7 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-300">
          <AppIcon name="activity" :size="14" />
        </div>
        <h2 class="text-sm font-semibold text-zinc-100">Job Pipeline</h2>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="!sessions || sessions.length === 0"
      class="text-center py-8 px-4 rounded-xl border border-dashed border-zinc-800/80 bg-zinc-950/30"
    >
      <AppIcon name="server" :size="20" class="mx-auto mb-2 text-zinc-600" />
      <p class="text-xs text-zinc-500">
        No active background workers. Launch a job to start creation.
      </p>
    </div>

    <!-- Sessions List -->
    <div v-else class="space-y-3">
      <div
        v-for="session in sessions"
        :key="session.id"
        class="bg-zinc-950/80 rounded-xl p-4 border border-zinc-800 hover:border-zinc-700/80 transition space-y-3"
      >
        <!-- Top Row -->
        <div class="flex items-center justify-between">
          <span class="font-mono text-xs font-semibold text-zinc-200 tracking-wide">{{ session.id }}</span>
          <span
            class="px-2 py-0.5 rounded text-[11px] font-mono font-medium"
            :class="getStatusBadgeClass(session.status)"
          >
            {{ session.status }}
          </span>
        </div>

        <!-- Progress Metrics -->
        <div>
          <div class="flex justify-between text-xs mb-1.5 font-mono">
            <span class="text-zinc-400">Progress</span>
            <span class="text-zinc-300">
              {{ session.progress?.current || 0 }} / {{ session.progress?.total || 0 }} ({{ getProgressPercent(session) }}%)
            </span>
          </div>

          <!-- Progress Bar -->
          <div class="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
            <div
              class="h-1.5 rounded-full transition-all duration-300"
              :class="session.status === 'failed' ? 'bg-rose-500' : 'bg-indigo-500'"
              :style="{ width: `${getProgressPercent(session)}%` }"
            ></div>
          </div>
        </div>

        <!-- Inline Stats Breakdown -->
        <div class="flex items-center justify-between text-xs font-mono pt-1 text-zinc-400 border-t border-zinc-900">
          <div>Success: <span class="text-emerald-400 font-semibold">{{ session.progress?.successes || 0 }}</span></div>
          <div>Failed: <span class="text-rose-400 font-semibold">{{ session.progress?.failures || 0 }}</span></div>
          <div>Yield: <span class="text-zinc-200 font-semibold">{{ (session.progress?.success_rate || 0).toFixed(1) }}%</span></div>
        </div>

        <!-- Actions -->
        <div v-if="session.status === 'running'" class="pt-1">
          <button
            @click="handleStop(session.id)"
            class="btn-danger w-full py-1.5 text-xs"
          >
            <AppIcon name="square" :size="13" class="mr-1.5" />
            <span>Terminate Session</span>
          </button>
        </div>
        <div v-else-if="canResume(session)" class="pt-1">
          <button
            @click="handleResume(session.id)"
            class="btn-secondary w-full py-1.5 text-xs border-indigo-500/30 text-indigo-400 hover:bg-indigo-950/40"
          >
            <AppIcon name="play" :size="13" class="mr-1.5" />
            <span>Resume Remaining ({{ (session.progress?.total || 0) - ((session.progress?.successes || 0) + (session.progress?.failures || 0)) }})</span>
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

const emit = defineEmits(['stop-session', 'resume-session'])

function getProgressPercent(session) {
  if (!session?.progress?.total) return 0
  const pct = (session.progress.current / session.progress.total) * 100
  return Math.min(100, Math.max(0, Number(pct.toFixed(1))))
}

function getStatusBadgeClass(status) {
  return SESSION_STATUS_STYLES[status]?.badge || 'bg-zinc-800 text-zinc-400 border-zinc-700'
}

function canResume(session) {
  const resumableStatuses = ['interrupted', 'stopped', 'failed', 'completed']
  if (!resumableStatuses.includes(session.status)) return false
  const total = session.progress?.total || 0
  const completed = (session.progress?.successes || 0) + (session.progress?.failures || 0)
  return total > completed
}

function handleStop(sessionId) {
  emit('stop-session', sessionId)
}

function handleResume(sessionId) {
  emit('resume-session', sessionId)
}
</script>
