<template>
  <div class="min-h-screen bg-zinc-950 text-zinc-100 selection:bg-indigo-600 selection:text-white">
    <router-view />
    <ToastContainer />
  </div>
</template>

<script setup>
import ToastContainer from './components/ToastContainer.vue'
</script>
