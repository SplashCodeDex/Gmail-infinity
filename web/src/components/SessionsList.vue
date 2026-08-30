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
      <div class="flex items-center space-x-2">
        <span
          v-if="activeSessions.length > 0"
          class="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-950/60 text-emerald-400 border border-emerald-800/40"
        >
          {{ activeSessions.length }} active
        </span>
        <span
          v-else
          class="text-xs text-zinc-500 font-mono"
        >
          Idle
        </span>
      </div>
    </div>

    <!-- Active Running Sessions -->
    <div v-if="activeSessions.length > 0" class="space-y-3">
      <div
        v-for="session in activeSessions"
        :key="session.id"
        class="bg-zinc-950 rounded-xl p-4 border border-zinc-800 space-y-3"
      >
        <!-- Top Row -->
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <span class="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
            <span class="font-mono text-xs font-semibold text-zinc-200 tracking-wide">{{ session.id }}</span>
          </div>
          <span
            class="px-2 py-0.5 rounded text-[11px] font-mono font-medium"
            :class="getStatusBadgeClass(session.status)"
          >
            {{ session.status }}
          </span>
        </div>

        <!-- Progress Bar & Metrics -->
        <div>
          <div class="flex justify-between text-xs mb-1.5 font-mono">
            <span class="text-zinc-400">Progress</span>
            <span class="text-zinc-200 font-medium">
              {{ session.progress?.current || 0 }} / {{ session.progress?.total || 0 }} ({{ getProgressPercent(session) }}%)
            </span>
          </div>

          <div class="w-full bg-zinc-800 rounded-full h-1 overflow-hidden">
            <div
              class="h-1 rounded-full bg-indigo-500 transition-all duration-300"
              :style="{ width: `${getProgressPercent(session)}%` }"
            ></div>
          </div>
        </div>

        <!-- Stats Breakdown -->
        <div class="flex items-center justify-between text-xs font-mono pt-1 text-zinc-400 border-t border-zinc-900">
          <div>Success: <span class="text-emerald-400">{{ session.progress?.successes || 0 }}</span></div>
          <div>Failed: <span class="text-rose-400">{{ session.progress?.failures || 0 }}</span></div>
          <div>Yield: <span class="text-zinc-200">{{ (session.progress?.success_rate || 0).toFixed(1) }}%</span></div>
        </div>

        <!-- Terminate Button -->
        <div class="pt-1">
          <button
            @click="handleStop(session.id)"
            class="btn-danger w-full py-1.5 text-xs font-medium"
          >
            <AppIcon name="square" :size="13" class="mr-1.5" />
            <span>Terminate Active Session</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State for Active Jobs -->
    <div
      v-else
      class="text-center py-6 px-4 rounded-xl border border-dashed border-zinc-800/80 bg-zinc-950/30"
    >
      <AppIcon name="server" :size="18" class="mx-auto mb-1.5 text-zinc-600" />
      <p class="text-xs text-zinc-500">
        No active background workers running.
      </p>
    </div>

    <!-- Recent Job History Section -->
    <div v-if="pastSessions.length > 0" class="pt-2 border-t border-zinc-800/80 space-y-2.5">
      <div class="flex items-center justify-between text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
        <span>Recent History</span>
        <span class="font-mono text-[10px] text-zinc-500">{{ pastSessions.length }} jobs</span>
      </div>

      <div class="space-y-1.5 max-h-48 overflow-y-auto pr-0.5 custom-scrollbar">
        <div
          v-for="session in pastSessions.slice(0, 4)"
          :key="session.id"
          class="flex items-center justify-between p-2.5 rounded-lg bg-zinc-950/50 border border-zinc-800/70 hover:border-zinc-700/60 transition text-xs"
        >
          <!-- Left info: ID + Status -->
          <div class="flex items-center space-x-2 min-w-0">
            <span
              class="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium shrink-0"
              :class="getStatusBadgeClass(session.status)"
            >
              {{ session.status }}
            </span>
            <span class="font-mono text-[11px] text-zinc-300 truncate max-w-[140px]" :title="session.id">
              {{ session.id }}
            </span>
          </div>

          <!-- Middle stats -->
          <div class="flex items-center space-x-3 font-mono text-[11px] text-zinc-400 shrink-0">
            <span>{{ session.progress?.successes || 0 }}/{{ session.progress?.total || 0 }}</span>
            <span
              :class="(session.progress?.success_rate || 0) > 0 ? 'text-emerald-400' : 'text-zinc-500'"
            >
              {{ (session.progress?.success_rate || 0).toFixed(0) }}%
            </span>
          </div>

          <!-- Right Action: Resume if incomplete -->
          <div class="shrink-0 ml-2">
            <button
              v-if="canResume(session)"
              @click="handleResume(session.id)"
              class="px-2 py-0.5 text-[11px] font-mono font-medium rounded bg-indigo-950/70 text-indigo-300 border border-indigo-800/40 hover:bg-indigo-900/60 hover:text-indigo-200 transition flex items-center space-x-1"
              :title="`Resume remaining ${getRemainingCount(session)} accounts`"
            >
              <AppIcon name="play" :size="10" />
              <span>Resume ({{ getRemainingCount(session) }})</span>
            </button>
            <span v-else class="text-zinc-600 text-[11px] font-mono pr-1">—</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { SESSION_STATUS_STYLES } from '../constants/config'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  sessions: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['stop-session', 'resume-session'])

const activeSessions = computed(() => {
  return props.sessions.filter(s => s.status === 'running' || s.status === 'initializing')
})

const pastSessions = computed(() => {
  return props.sessions.filter(s => s.status !== 'running' && s.status !== 'initializing')
})

function getProgressPercent(session) {
  if (!session?.progress?.total) return 0
  const pct = (session.progress.current / session.progress.total) * 100
  return Math.min(100, Math.max(0, Number(pct.toFixed(1))))
}

function getStatusBadgeClass(status) {
  return SESSION_STATUS_STYLES[status]?.badge || 'bg-zinc-800 text-zinc-400 border-zinc-700'
}

function getRemainingCount(session) {
  const total = session.progress?.total || session.num_accounts || 0
  const completed = (session.progress?.successes || 0) + (session.progress?.failures || 0)
  return Math.max(0, total - completed)
}

function canResume(session) {
  const resumableStatuses = ['interrupted', 'stopped', 'failed', 'completed']
  if (!resumableStatuses.includes(session.status)) return false
  return getRemainingCount(session) > 0
}

function handleStop(sessionId) {
  emit('stop-session', sessionId)
}

function handleResume(sessionId) {
  emit('resume-session', sessionId)
}
</script>
