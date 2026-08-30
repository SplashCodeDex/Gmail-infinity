<template>
  <div class="surface-card px-4 py-3 hover:border-zinc-700 transition-colors flex items-center justify-between">
    <div class="min-w-0 pr-3">
      <div class="text-[11px] font-medium text-zinc-400 truncate">{{ title }}</div>
      <div class="text-xl font-bold font-mono tracking-tight text-zinc-100 mt-0.5">
        {{ value }}
      </div>
      <div v-if="subtitle" class="text-[11px] text-zinc-500 font-mono truncate mt-0.5">
        {{ subtitle }}
      </div>
    </div>

    <div class="text-zinc-500 shrink-0">
      <AppIcon :name="icon" :size="20" />
    </div>
  </div>
</template>

<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  title: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number],
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
  icon: {
    type: String,
    default: 'activity',
  },
})
</script>
