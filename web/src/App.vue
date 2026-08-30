<template>
  <div class="min-h-screen bg-gray-900 text-gray-100">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useWebSocketStore } from './stores/websocket'

const ws = useWebSocketStore()

onMounted(() => {
  ws.connect()
})
</script>
