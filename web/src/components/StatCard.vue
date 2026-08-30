<template>
  <div class="bg-zinc-900/90 border border-zinc-800/90 rounded-xl px-4 py-3 hover:border-zinc-700/80 transition-colors flex items-center justify-between">
    <div class="min-w-0 pr-3">
      <div class="text-[11px] font-medium text-zinc-400 truncate">{{ title }}</div>
      <div class="text-xl font-bold font-mono tracking-tight text-zinc-100 mt-0.5">
        {{ value }}
      </div>
      <div v-if="subtitle" class="text-[11px] text-zinc-500 font-mono truncate mt-0.5">
        {{ subtitle }}
      </div>
    </div>

    <div
      class="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 border"
      :class="[iconBgClass, iconBorderClass, iconTextClass]"
    >
      <AppIcon :name="icon" :size="17" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({
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
  variant: {
    type: String,
    default: 'indigo',
  },
})

const colorMap = {
  indigo: {
    iconText: 'text-indigo-400',
    iconBg: 'bg-indigo-950/40',
    iconBorder: 'border-indigo-800/60',
  },
  emerald: {
    iconText: 'text-emerald-400',
    iconBg: 'bg-emerald-950/40',
    iconBorder: 'border-emerald-800/60',
  },
  amber: {
    iconText: 'text-amber-400',
    iconBg: 'bg-amber-950/40',
    iconBorder: 'border-amber-800/60',
  },
  rose: {
    iconText: 'text-rose-400',
    iconBg: 'bg-rose-950/40',
    iconBorder: 'border-rose-800/60',
  },
  cyan: {
    iconText: 'text-cyan-400',
    iconBg: 'bg-cyan-950/40',
    iconBorder: 'border-cyan-800/60',
  },
}

const currentVariant = computed(() => colorMap[props.variant] || colorMap.indigo)
const iconTextClass = computed(() => currentVariant.value.iconText)
const iconBgClass = computed(() => currentVariant.value.iconBg)
const iconBorderClass = computed(() => currentVariant.value.iconBorder)
</script>
