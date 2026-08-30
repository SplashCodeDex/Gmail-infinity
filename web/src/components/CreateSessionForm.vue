<template>
  <div class="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-6">
    <h2 class="text-xl font-bold mb-6 flex items-center">
      <span class="mr-3">➕</span>
      Create New Session
    </h2>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <!-- Number of Accounts -->
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          🔢 Number of Accounts
        </label>
        <input
          v-model.number="form.num_accounts"
          type="number"
          min="1"
          max="1000"
          class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          required
        />
        <p class="text-xs text-gray-400 mt-1">Min: 1, Max: 1000</p>
      </div>

      <!-- Concurrent Workers -->
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          ⚙️ Concurrent Workers
        </label>
        <select
          v-model.number="form.concurrent"
          class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
        >
          <option :value="1">1 Worker (Safe)</option>
          <option :value="2">2 Workers (Balanced)</option>
          <option :value="3">3 Workers (Fast)</option>
          <option :value="5">5 Workers (Maximum)</option>
        </select>
      </div>

      <!-- Toggles -->
      <div class="space-y-3">
        <ToggleSwitch
          v-model="form.use_sms"
          label="SMS Verification"
          icon="📱"
          color="blue"
        />
        <ToggleSwitch
          v-model="form.use_proxies"
          label="Use Proxies"
          icon="🛡️"
          color="green"
        />
        <ToggleSwitch
          v-model="form.warmup"
          label="Account Warming"
          icon="🔥"
          color="orange"
        />
        <ToggleSwitch
          v-model="form.adaptive"
          label="Adaptive AI"
          icon="🧠"
          color="purple"
        />
      </div>

      <!-- Export Format -->
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          💾 Export Format
        </label>
        <select
          v-model="form.export_format"
          class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
        >
          <option value="json">JSON</option>
          <option value="csv">CSV</option>
          <option value="txt">TXT</option>
          <option value="all">All Formats</option>
        </select>
      </div>

      <!-- Submit Button -->
      <button
        type="submit"
        :disabled="loading"
        class="w-full gradient-bg text-white font-bold py-3 px-6 rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
      >
        <span v-if="!loading">🚀</span>
        <span v-else class="animate-spin">⚙️</span>
        <span>{{ loading ? 'Starting...' : 'Start Creating Accounts' }}</span>
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useAppStore } from '../stores/app'
import ToggleSwitch from './ToggleSwitch.vue'

const emit = defineEmits(['session-started'])
const app = useAppStore()

const loading = ref(false)

const form = reactive({
  num_accounts: 5,
  concurrent: 1,
  use_sms: false,
  use_proxies: true,
  warmup: true,
  adaptive: true,
  export_format: 'json',
  auto_recover: true
})

async function handleSubmit() {
  loading.value = true
  try {
    await app.startSession(form)
    emit('session-started')

    // Reset form (optional)
    // form.num_accounts = 5
  } catch (error) {
    console.error('Failed to start session:', error)
    alert('Failed to start session: ' + error.message)
  } finally {
    loading.value = false
  }
}
</script>
