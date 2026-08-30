<template>
  <div class="flex items-center justify-between p-3.5 bg-zinc-950/60 border border-zinc-800/80 rounded-xl hover:border-zinc-700/80 transition-colors">
    <div class="flex items-center space-x-3 min-w-0 pr-3">
      <div
        class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border"
        :class="modelValue ? 'bg-zinc-800 border-zinc-700 text-indigo-400' : 'bg-zinc-900 border-zinc-800 text-zinc-500'"
      >
        <AppIcon :name="icon" :size="16" />
      </div>
      <div class="min-w-0">
        <div class="text-sm font-medium text-zinc-200 truncate">{{ label }}</div>
        <div v-if="description" class="text-xs text-zinc-500 truncate">{{ description }}</div>
      </div>
    </div>

    <!-- Switch -->
    <label class="relative inline-flex items-center cursor-pointer shrink-0">
      <input
        type="checkbox"
        :checked="modelValue"
        @change="$emit('update:modelValue', $event.target.checked)"
        class="sr-only peer"
      />
      <div
        class="w-11 h-6 bg-zinc-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-zinc-100 after:border-zinc-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all transition-colors"
        :class="modelValue ? 'bg-indigo-600' : 'bg-zinc-800'"
      ></div>
    </label>
  </div>
</template>

<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
  label: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: '',
  },
  icon: {
    type: String,
    default: 'sliders',
  },
  color: {
    type: String,
    default: 'indigo',
  },
})

defineEmits(['update:modelValue'])
</script>
