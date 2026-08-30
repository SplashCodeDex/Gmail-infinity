<template>
  <div class="surface-card p-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-5 border-b border-zinc-800 gap-3">
      <div class="flex items-center space-x-3">
        <div class="w-9 h-9 rounded-lg bg-indigo-950/60 border border-indigo-800/80 flex items-center justify-center text-indigo-400">
          <AppIcon name="shield" :size="18" />
        </div>
        <div>
          <h2 class="text-base font-bold text-zinc-100 flex items-center space-x-2">
            <span>Proxy Network Telemetry & Pool Hub</span>
            <span class="px-2 py-0.5 rounded-full text-xs font-mono bg-zinc-800 text-zinc-300 border border-zinc-700">
              {{ allProxies.length || appStore.stats?.proxies?.total || 0 }} Endpoints
            </span>
          </h2>
          <p class="text-xs text-zinc-400">Health verification, latency benchmarks, public harvesting & manual pool ingestion</p>
        </div>
      </div>

      <!-- Header Action Controls -->
      <div class="flex flex-wrap items-center gap-2">
        <!-- Fetch Public Proxies Button -->
        <button
          @click="handleFetchPublic"
          :disabled="isFetchingPublic"
          class="btn-secondary py-1.5 px-3 text-xs flex items-center space-x-1.5"
          title="Scrape and harvest fresh public SOCKS5/HTTP proxies"
        >
          <AppIcon v-if="!isFetchingPublic" name="download" :size="13" />
          <svg v-else class="animate-spin h-3 w-3 text-indigo-400" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
          </svg>
          <span>{{ isFetchingPublic ? 'Harvesting...' : 'Fetch Public' }}</span>
        </button>

        <!-- Import / Paste Modal Trigger -->
        <button
          @click="showImportModal = true"
          class="btn-secondary py-1.5 px-3 text-xs flex items-center space-x-1.5"
        >
          <AppIcon name="plus" :size="13" />
          <span>Import / Paste</span>
        </button>

        <!-- Run Latency Test Button -->
        <button
          @click="runProxyTest"
          :disabled="isTesting || allProxies.length === 0"
          class="btn-primary py-1.5 px-3 text-xs flex items-center space-x-1.5"
        >
          <AppIcon v-if="!isTesting" name="activity" :size="13" />
          <svg v-else class="animate-spin h-3.5 w-3.5 text-white" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
          </svg>
          <span>{{ isTesting ? 'Benchmarking...' : 'Test All' }}</span>
        </button>
      </div>
    </div>

    <!-- Metrics Cards (Solid Colors, Zero Gradient) -->
    <div class="grid grid-cols-3 gap-3 mb-5">
      <div class="bg-zinc-950/80 p-3.5 rounded-xl border border-zinc-800 text-center">
        <div class="text-[11px] font-mono uppercase tracking-wider text-zinc-400">Total Configured</div>
        <div class="text-xl font-bold font-mono text-zinc-100 mt-0.5">
          {{ proxyData.total || allProxies.length || 0 }}
        </div>
      </div>

      <div class="bg-zinc-950/80 p-3.5 rounded-xl border border-emerald-800/60 text-center">
        <div class="text-[11px] font-mono uppercase tracking-wider text-emerald-400">Healthy & Online</div>
        <div class="text-xl font-bold font-mono text-emerald-400 mt-0.5">
          {{ proxyData.healthy || appStore.stats?.proxies?.healthy || 0 }}
        </div>
      </div>

      <div class="bg-zinc-950/80 p-3.5 rounded-xl border border-rose-800/60 text-center">
        <div class="text-[11px] font-mono uppercase tracking-wider text-rose-400">Unreachable / Offline</div>
        <div class="text-xl font-bold font-mono text-rose-400 mt-0.5">
          {{ proxyData.unhealthy || 0 }}
        </div>
      </div>
    </div>

    <!-- Proxy List Table/View -->
    <div class="rounded-xl border border-zinc-800 bg-zinc-950/50 overflow-hidden">
      <div class="p-3 border-b border-zinc-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
        <div class="relative w-full sm:w-64">
          <input
            v-model="search"
            type="text"
            placeholder="Filter proxy IP / port..."
            class="w-full pl-8 pr-3 py-1 bg-zinc-900 border border-zinc-700 rounded-lg text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-indigo-500 font-mono"
          />
          <AppIcon name="search" :size="13" class="absolute left-2.5 top-1.5 text-zinc-500" />
        </div>

        <div class="flex items-center space-x-2">
          <!-- Filter Tabs -->
          <div class="flex items-center space-x-1">
            <button
              @click="filterMode = 'all'"
              class="px-2.5 py-1 rounded text-[11px] font-mono transition"
              :class="filterMode === 'all' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300'"
            >
              All
            </button>
            <button
              @click="filterMode = 'healthy'"
              class="px-2.5 py-1 rounded text-[11px] font-mono transition"
              :class="filterMode === 'healthy' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'text-zinc-500 hover:text-zinc-300'"
            >
              Healthy
            </button>
            <button
              @click="filterMode = 'unhealthy'"
              class="px-2.5 py-1 rounded text-[11px] font-mono transition"
              :class="filterMode === 'unhealthy' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'text-zinc-500 hover:text-zinc-300'"
            >
              Unhealthy
            </button>
          </div>

          <!-- Clear Pool Button -->
          <button
            v-if="allProxies.length > 0"
            @click="handleClearPool"
            class="p-1.5 text-zinc-500 hover:text-rose-400 hover:bg-zinc-900 rounded transition"
            title="Clear all proxies from pool"
          >
            <AppIcon name="trash-2" :size="14" />
          </button>
        </div>
      </div>

      <!-- Proxy Rows -->
      <div class="divide-y divide-zinc-800/80 max-h-96 overflow-y-auto font-mono text-xs">
        <div
          v-if="filteredProxies.length === 0"
          class="p-8 text-center text-zinc-500"
        >
          <AppIcon name="shield" :size="24" class="mx-auto mb-2 text-zinc-600" />
          <span v-if="allProxies.length === 0">No proxies configured. Click "Import / Paste" or "Fetch Public" to populate pool.</span>
          <span v-else>No proxies match filter "{{ search }}"</span>
        </div>

        <div
          v-for="(p, i) in filteredProxies"
          :key="i"
          class="p-3 flex items-center justify-between hover:bg-zinc-900/60 transition group"
        >
          <div class="flex items-center space-x-3 min-w-0 pr-2">
            <span
              class="w-2 h-2 rounded-full shrink-0"
              :class="p.healthy !== false ? 'bg-emerald-500' : 'bg-rose-500'"
            ></span>
            <span class="text-zinc-200 truncate">{{ p.proxy }}</span>
          </div>

          <div class="flex items-center space-x-3 shrink-0">
            <!-- Latency Badge -->
            <span
              v-if="p.latency_ms"
              class="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800"
            >
              {{ p.latency_ms }} ms
            </span>
            <span
              v-else-if="p.healthy === false"
              class="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-950 text-rose-300 border border-rose-800"
            >
              Offline
            </span>
            <span
              v-else
              class="px-2 py-0.5 rounded text-[11px] font-mono text-zinc-500 bg-zinc-900 border border-zinc-800"
            >
              Untested
            </span>

            <!-- Copy Button -->
            <button
              @click="copyProxy(p.proxy)"
              class="p-1 text-zinc-500 hover:text-zinc-200 rounded opacity-0 group-hover:opacity-100 transition"
              title="Copy proxy string"
            >
              <AppIcon name="copy" :size="13" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Import / Paste Modal -->
    <div
      v-if="showImportModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
    >
      <div class="bg-zinc-900 border border-zinc-700 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-zinc-800">
          <div class="flex items-center space-x-2">
            <AppIcon name="plus" :size="18" class="text-indigo-400" />
            <h3 class="text-base font-bold text-zinc-100">Import Proxies</h3>
          </div>
          <button @click="showImportModal = false" class="text-zinc-500 hover:text-zinc-300">
            <AppIcon name="x" :size="16" />
          </button>
        </div>

        <div>
          <label class="block text-xs font-medium text-zinc-300 mb-1.5">
            Paste proxy list (One per line: <code class="text-indigo-400">host:port</code> or <code class="text-indigo-400">user:pass@host:port</code>)
          </label>
          <textarea
            v-model="importText"
            rows="7"
            placeholder="127.0.0.1:8080&#10;user:password@proxy.example.com:8000&#10;socks5://192.168.1.50:1080"
            class="form-input font-mono text-xs resize-none"
          ></textarea>
        </div>

        <div class="flex items-center justify-between pt-2">
          <label class="flex items-center space-x-2 text-xs text-zinc-300 cursor-pointer">
            <input
              type="checkbox"
              v-model="replaceExisting"
              class="rounded bg-zinc-950 border-zinc-700 text-indigo-600 focus:ring-0"
            />
            <span>Replace existing pool</span>
          </label>

          <div class="flex items-center space-x-2">
            <button
              @click="showImportModal = false"
              class="btn-secondary py-1.5 px-3 text-xs"
            >
              Cancel
            </button>
            <button
              @click="handleImportSubmit"
              :disabled="!importText.trim() || isImporting"
              class="btn-primary py-1.5 px-4 text-xs"
            >
              {{ isImporting ? 'Importing...' : 'Save Proxies' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAppStore } from '../stores/app'
import { useToastStore } from '../stores/toast'
import AppIcon from './AppIcon.vue'

const appStore = useAppStore()
const toast = useToastStore()

const isTesting = ref(false)
const isFetchingPublic = ref(false)
const isImporting = ref(false)
const filterMode = ref('all')
const search = ref('')
const showImportModal = ref(false)
const importText = ref('')
const replaceExisting = ref(false)

const allProxiesList = ref([])

const proxyData = reactive({
  total: 0,
  healthy: 0,
  unhealthy: 0,
  proxies: [],
})

const allProxies = computed(() => {
  if (proxyData.proxies.length > 0) return proxyData.proxies
  return allProxiesList.value.map(p => ({ proxy: p, healthy: null, latency_ms: null }))
})

const filteredProxies = computed(() => {
  let list = allProxies.value

  if (filterMode.value === 'healthy') {
    list = list.filter(p => p.healthy === true)
  } else if (filterMode.value === 'unhealthy') {
    list = list.filter(p => p.healthy === false)
  }

  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(p => (p.proxy || '').toLowerCase().includes(q))
  }

  return list
})

onMounted(async () => {
  await loadProxies()
})

async function loadProxies() {
  const data = await appStore.fetchProxiesList()
  if (data?.list) {
    allProxiesList.value = data.list
  }
}

async function runProxyTest() {
  isTesting.value = true
  try {
    const res = await appStore.testProxies()
    if (res) {
      proxyData.total = res.total || 0
      proxyData.healthy = res.healthy || 0
      proxyData.unhealthy = res.unhealthy || 0
      proxyData.proxies = res.proxies || []
    }
  } finally {
    isTesting.value = false
  }
}

async function handleFetchPublic() {
  isFetchingPublic.value = true
  try {
    await appStore.fetchPublicProxies()
    await loadProxies()
  } finally {
    isFetchingPublic.value = false
  }
}

async function handleImportSubmit() {
  isImporting.value = true
  try {
    await appStore.importProxies(importText.value, replaceExisting.value)
    importText.value = ''
    showImportModal.value = false
    await loadProxies()
  } finally {
    isImporting.value = false
  }
}

async function handleClearPool() {
  if (confirm('Clear all proxies from memory and disk?')) {
    await appStore.clearProxies()
    proxyData.proxies = []
    allProxiesList.value = []
  }
}

async function copyProxy(text) {
  try {
    await navigator.clipboard.writeText(text)
    toast.success(`Copied: ${text}`, 'Clipboard')
  } catch {
    toast.error('Failed to copy proxy string')
  }
}
</script>
