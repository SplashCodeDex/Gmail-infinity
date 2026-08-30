<template>
  <div class="stat-card bg-gray-800 rounded-xl p-6 shadow-xl border border-gray-700">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-gray-400 text-sm mb-1">{{ title }}</p>
        <h3 :class="['text-3xl font-bold', textColor]">{{ value }}</h3>
      </div>
      <div :class="['p-4 rounded-full', bgColor]">
        <span class="text-2xl">{{ icon }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  icon: {
    type: String,
    required: true
  },
  color: {
    type: String,
    default: 'blue'
  }
})

const colorMap = {
  blue: { text: 'text-blue-400', bg: 'bg-blue-500/20' },
  green: { text: 'text-green-400', bg: 'bg-green-500/20' },
  purple: { text: 'text-purple-400', bg: 'bg-purple-500/20' },
  yellow: { text: 'text-yellow-400', bg: 'bg-yellow-500/20' },
  red: { text: 'text-red-400', bg: 'bg-red-500/20' },
}

const textColor = computed(() => colorMap[props.color]?.text || colorMap.blue.text)
const bgColor = computed(() => colorMap[props.color]?.bg || colorMap.blue.bg)
</script>
