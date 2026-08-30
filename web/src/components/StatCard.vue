<template>
  <div class="stat-card flex flex-col justify-between">
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-semibold uppercase tracking-wider text-zinc-400">{{ title }}</span>
      <div
        class="w-10 h-10 rounded-lg flex items-center justify-center border"
        :class="[iconBgClass, iconBorderClass, iconTextClass]"
      >
        <AppIcon :name="icon" :size="20" />
      </div>
    </div>

    <div class="flex items-baseline justify-between mt-1">
      <div class="text-2xl font-bold font-mono tracking-tight" :class="valueTextClass">
        {{ value }}
      </div>
      <div v-if="subtitle" class="text-xs text-zinc-500 font-mono">
        {{ subtitle }}
      </div>
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
    default: 'indigo', // 'indigo', 'emerald', 'amber', 'rose', 'cyan'
  },
})

const colorMap = {
  indigo: {
    text: 'text-indigo-400',
    iconText: 'text-indigo-400',
    iconBg: 'bg-indigo-950/60',
    iconBorder: 'border-indigo-800/80',
  },
  emerald: {
    text: 'text-emerald-400',
    iconText: 'text-emerald-400',
    iconBg: 'bg-emerald-950/60',
    iconBorder: 'border-emerald-800/80',
  },
  amber: {
    text: 'text-amber-400',
    iconText: 'text-amber-400',
    iconBg: 'bg-amber-950/60',
    iconBorder: 'border-amber-800/80',
  },
  rose: {
    text: 'text-rose-400',
    iconText: 'text-rose-400',
    iconBg: 'bg-rose-950/60',
    iconBorder: 'border-rose-800/80',
  },
  cyan: {
    text: 'text-cyan-400',
    iconText: 'text-cyan-400',
    iconBg: 'bg-cyan-950/60',
    iconBorder: 'border-cyan-800/80',
  },
}

const currentVariant = computed(() => colorMap[props.variant] || colorMap.indigo)
const valueTextClass = computed(() => currentVariant.value.text)
const iconTextClass = computed(() => currentVariant.value.iconText)
const iconBgClass = computed(() => currentVariant.value.iconBg)
const iconBorderClass = computed(() => currentVariant.value.iconBorder)
</script>
