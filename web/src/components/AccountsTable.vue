<template>
  <div class="surface-card p-6">
    <!-- Header & Search Toolbar -->
    <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-5 border-b border-zinc-800 gap-4">
      <div class="flex items-center space-x-3">
        <div class="w-9 h-9 rounded-lg bg-indigo-950/60 border border-indigo-800/80 flex items-center justify-center text-indigo-400">
          <AppIcon name="database" :size="18" />
        </div>
        <div>
          <h2 class="text-base font-bold text-zinc-100 flex items-center space-x-2">
            <span>Accounts Vault</span>
            <span class="px-2 py-0.5 rounded-full text-xs font-mono bg-zinc-800 text-zinc-300 border border-zinc-700">
              {{ accounts.length }} Total
            </span>
          </h2>
          <p class="text-xs text-zinc-400">Stored credentials & registered account database</p>
        </div>
      </div>

      <!-- Controls -->
      <div class="flex flex-wrap items-center gap-2.5">
        <!-- Search Input -->
        <div class="relative w-full sm:w-64">
          <input
            v-model="search"
            type="text"
            placeholder="Search email or username..."
            class="w-full pl-8 pr-3 py-1.5 bg-zinc-950 border border-zinc-700 rounded-lg text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-indigo-500 font-mono"
          />
          <AppIcon name="search" :size="14" class="absolute left-2.5 top-2 text-zinc-500" />
        </div>

        <!-- Health Check -->
        <button
          @click="appStore.checkAccountsHealth()"
          :disabled="appStore.checkingHealth"
          class="btn-secondary py-1.5 text-xs flex items-center space-x-1.5 disabled:opacity-50 disabled:cursor-wait"
          title="Verify accounts are still alive via Gmail IMAP"
        >
          <AppIcon name="activity" :size="14" />
          <span>{{ appStore.checkingHealth ? 'Checking…' : 'Health Check' }}</span>
        </button>

        <!-- Export Dropdown -->
        <div class="relative">
          <button
            @click="showExportMenu = !showExportMenu"
            class="btn-secondary py-1.5 text-xs flex items-center space-x-1.5"
          >
            <AppIcon name="download" :size="14" />
            <span>Export</span>
          </button>

          <div
            v-if="showExportMenu"
            class="absolute right-0 mt-1 w-44 bg-zinc-900 border border-zinc-700 rounded-xl shadow-2xl py-1 z-30 font-mono text-xs"
          >
            <button
              v-for="fmt in EXPORT_FORMATS"
              :key="fmt.value"
              @click="handleExport(fmt.value)"
              class="w-full text-left px-3 py-2 hover:bg-zinc-800 text-zinc-200 transition flex items-center justify-between"
            >
              <span>{{ fmt.label }}</span>
            </button>
          </div>
        </div>

        <!-- Refresh Action -->
        <button
          @click="appStore.fetchAccounts"
          class="p-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-zinc-300 transition"
          title="Reload accounts list"
        >
          <AppIcon name="refresh-cw" :size="14" />
        </button>
      </div>
    </div>

    <!-- Accounts Table Container -->
    <div class="overflow-x-auto rounded-xl border border-zinc-800">
      <table class="w-full text-left text-xs">
        <thead class="bg-zinc-950/80 text-zinc-400 font-mono uppercase tracking-wider text-[11px] border-b border-zinc-800">
          <tr>
            <th class="py-3 px-4">Account Identifier</th>
            <th class="py-3 px-4">Password</th>
            <th class="py-3 px-4">Recovery Email</th>
            <th class="py-3 px-4">Created At</th>
            <th class="py-3 px-4">Health</th>
            <th class="py-3 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-800/80 font-mono">
          <tr
            v-if="filteredAccounts.length === 0"
            class="text-center text-zinc-500 py-8"
          >
            <td colspan="5" class="py-8 text-center">
              <div class="flex flex-col items-center justify-center space-y-1">
                <AppIcon name="database" :size="24" class="text-zinc-600 mb-1" />
                <span v-if="accounts.length === 0">No accounts stored yet. Launch a session to populate vault.</span>
                <span v-else>No accounts match search "{{ search }}"</span>
              </div>
            </td>
          </tr>

          <tr
            v-for="(acc, i) in filteredAccounts"
            :key="i"
            class="hover:bg-zinc-900/60 transition-colors group"
          >
            <!-- Email -->
            <td class="py-3 px-4 font-semibold text-zinc-100">
              <div class="flex items-center space-x-2">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                <span>{{ acc.email || acc.username }}</span>
              </div>
            </td>

            <!-- Password -->
            <td class="py-3 px-4 text-zinc-400 group-hover:text-zinc-200">
              <span class="bg-zinc-950 px-2 py-0.5 rounded border border-zinc-800 text-zinc-300">
                {{ showPassword[i] ? acc.password : '••••••••••••' }}
              </span>
            </td>

            <!-- Recovery -->
            <td class="py-3 px-4 text-zinc-400">
              {{ acc.recovery_email || '—' }}
            </td>

            <!-- Created At -->
            <td class="py-3 px-4 text-zinc-500 text-[11px]">
              {{ acc.created_at || 'Saved' }}
            </td>

            <!-- Health -->
            <td class="py-3 px-4">
              <span
                v-if="healthFor(acc)"
                :class="healthBadgeClass(healthFor(acc).status)"
                class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono border"
                :title="healthFor(acc).message"
              >
                {{ healthFor(acc).status }}
              </span>
              <span v-else class="text-zinc-600 text-[11px]">—</span>
            </td>

            <!-- Actions -->
            <td class="py-3 px-4 text-right">
              <div class="flex items-center justify-end space-x-1.5">
                <button
                  @click="appStore.checkAccountsHealth([acc.email || acc.username])"
                  :disabled="appStore.checkingHealth"
                  class="p-1 text-zinc-400 hover:text-emerald-400 hover:bg-zinc-800 rounded transition disabled:opacity-50"
                  title="Check this account via IMAP"
                >
                  <AppIcon name="activity" :size="13" />
                </button>
                <button
                  @click="togglePassword(i)"
                  class="p-1 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded transition"
                  :title="showPassword[i] ? 'Hide Password' : 'Show Password'"
                >
                  <AppIcon :name="showPassword[i] ? 'lock' : 'eye'" :size="13" />
                </button>
                <button
                  @click="copyCreds(acc)"
                  class="p-1 text-zinc-400 hover:text-indigo-400 hover:bg-zinc-800 rounded transition"
                  title="Copy formatted email:pass"
                >
                  <AppIcon name="copy" :size="13" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useAppStore } from '../stores/app'
import { useToastStore } from '../stores/toast'
import { EXPORT_FORMATS } from '../constants/config'
import AppIcon from './AppIcon.vue'

const appStore = useAppStore()
const toast = useToastStore()

const search = ref('')
const showExportMenu = ref(false)
const showPassword = reactive({})

const accounts = computed(() => appStore.accounts || [])

const filteredAccounts = computed(() => {
  if (!search.value.trim()) return accounts.value
  const q = search.value.toLowerCase()
  return accounts.value.filter(a => {
    const email = (a.email || a.username || '').toLowerCase()
    const rec = (a.recovery_email || '').toLowerCase()
    return email.includes(q) || rec.includes(q)
  })
})

function togglePassword(index) {
  showPassword[index] = !showPassword[index]
}

async function copyCreds(acc) {
  const line = `${acc.email || acc.username}:${acc.password}${acc.recovery_email ? ':' + acc.recovery_email : ''}`
  try {
    await navigator.clipboard.writeText(line)
    toast.success(`Copied: ${acc.email || acc.username}`, 'Clipboard')
  } catch {
    toast.error('Failed to copy credentials', 'Clipboard')
  }
}

async function handleExport(format) {
  showExportMenu.value = false
  await appStore.exportAccounts(format)
}

function healthFor(acc) {
  const email = acc.email || acc.username
  return appStore.healthResults[email] || null
}

const HEALTH_BADGES = {
  active: 'bg-emerald-950/60 text-emerald-400 border-emerald-800',
  password_changed: 'bg-amber-950/60 text-amber-400 border-amber-800',
  locked: 'bg-red-950/60 text-red-400 border-red-800',
  suspended: 'bg-red-950/60 text-red-400 border-red-800',
  error: 'bg-zinc-900 text-zinc-400 border-zinc-700',
  network_error: 'bg-zinc-900 text-zinc-400 border-zinc-700',
  unknown: 'bg-zinc-900 text-zinc-400 border-zinc-700',
}

function healthBadgeClass(status) {
  return HEALTH_BADGES[status] || HEALTH_BADGE_CLASSES_FALLBACK
}

const HEALTH_BADGE_CLASSES_FALLBACK = 'bg-zinc-900 text-zinc-400 border-zinc-700'
</script>
