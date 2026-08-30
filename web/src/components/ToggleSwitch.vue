<template>
  <div class="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
    <div class="flex items-center">
      <span class="mr-3">{{ icon }}</span>
      <span class="text-sm font-medium">{{ label }}</span>
    </div>
    <label class="relative inline-flex items-center cursor-pointer">
      <input
        type="checkbox"
        :checked="modelValue"
        @change="$emit('update:modelValue', $event.target.checked)"
        class="sr-only peer"
      />
      <div
        :class="[
          'w-11 h-6 rounded-full peer',
          'peer-focus:ring-2 peer-focus:ring-purple-500',
          'after:content-[\"\"] after:absolute after:top-[2px] after:left-[2px]',
          'after:bg-white after:rounded-full after:h-5 after:w-5',
          'after:transition-all',
          'peer-checked:after:translate-x-full peer-checked:after:border-white',
          bgColor
        ]"
      ></div>
    </label>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  label: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    default: '⚙️'
  },
  color: {
    type: String,
    default: 'purple'
  }
})

defineEmits(['update:modelValue'])

const colorMap = {
  blue: 'bg-gray-600 peer-checked:bg-blue-600',
  green: 'bg-gray-600 peer-checked:bg-green-600',
  purple: 'bg-gray-600 peer-checked:bg-purple-600',
  orange: 'bg-gray-600 peer-checked:bg-orange-600',
  red: 'bg-gray-600 peer-checked:bg-red-600',
}

const bgColor = computed(() => colorMap[props.color] || colorMap.purple)
</script>
