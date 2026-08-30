<template>
  <div class="surface-card p-5 space-y-4">
    <!-- Header & Search Toolbar -->
    <div class="flex flex-col md:flex-row md:items-center justify-between pb-3.5 border-b border-zinc-800 gap-3">
      <div class="flex items-center space-x-2.5">
        <div class="w-7 h-7 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-300">
          <AppIcon name="database" :size="14" />
        </div>
        <h2 class="text-sm font-semibold text-zinc-100">Accounts Vault</h2>
      </div>

      <!-- Controls -->
      <div class="flex flex-wrap items-center gap-1.5">
        <!-- Search Input -->
        <div class="relative w-full sm:w-56">
          <input
            v-model="search"
            type="text"
            placeholder="Filter accounts..."
            class="w-full pl-7 pr-2.5 py-1 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 font-mono"
          />
          <AppIcon name="search" :size="11" class="absolute left-2.5 top-1.5 text-zinc-500" />
        </div>

        <!-- Health Check -->
        <button
          @click="appStore.checkAccountsHealth()"
          :disabled="appStore.checkingHealth"
          class="btn-secondary py-1 px-2.5 text-xs flex items-center space-x-1.5 disabled:opacity-50"
          title="Verify accounts are still alive via Gmail IMAP"
        >
          <AppIcon name="activity" :size="12" />
          <span>{{ appStore.checkingHealth ? 'Checking…' : 'Health Check' }}</span>
        </button>

        <!-- Export Dropdown -->
        <div class="relative">
          <button
            @click="showExportMenu = !showExportMenu"
            class="btn-secondary py-1 px-2.5 text-xs flex items-center space-x-1.5"
          >
            <AppIcon name="download" :size="12" />
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
          class="p-1 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-zinc-300 transition"
          title="Reload accounts list"
        >
          <AppIcon name="refresh-cw" :size="13" />
        </button>
      </div>
    </div>

    <!-- Accounts Table Container -->
    <div class="overflow-x-auto rounded-xl border border-zinc-800">
      <table class="w-full text-left text-xs">
        <thead class="bg-zinc-950 text-zinc-400 font-mono uppercase text-[11px] border-b border-zinc-800">
          <tr>
            <th class="py-2.5 px-4">Account</th>
            <th class="py-2.5 px-4">Password</th>
            <th class="py-2.5 px-4">Recovery Email</th>
            <th class="py-2.5 px-4">Created</th>
            <th class="py-2.5 px-4">Health</th>
            <th class="py-2.5 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-800/80 font-mono">
          <tr
            v-if="filteredAccounts.length === 0"
            class="text-center text-zinc-500 py-8"
          >
            <td colspan="6" class="py-8 text-center">
              <div class="flex flex-col items-center justify-center space-y-1">
                <AppIcon name="database" :size="20" class="text-zinc-600 mb-1" />
                <span v-if="accounts.length === 0">No accounts stored.</span>
                <span v-else>No accounts match search</span>
              </div>
            </td>
          </tr>

          <tr
            v-for="(acc, i) in filteredAccounts"
            :key="i"
            class="hover:bg-zinc-900/60 transition-colors group"
          >
            <!-- Email -->
            <td class="py-2.5 px-4 font-semibold text-zinc-100">
              {{ acc.email || acc.username }}
            </td>

            <!-- Password -->
            <td class="py-2.5 px-4 text-zinc-400">
              <span>{{ showPassword[i] ? acc.password : '••••••••••••' }}</span>
            </td>

            <!-- Recovery -->
            <td class="py-2.5 px-4 text-zinc-400">
              {{ acc.recovery_email || '—' }}
            </td>

            <!-- Created At -->
            <td class="py-2.5 px-4 text-zinc-500 text-[11px]">
              {{ acc.created_at || 'Saved' }}
            </td>

            <!-- Health -->
            <td class="py-2.5 px-4">
              <span
                v-if="healthFor(acc)"
                :class="healthTextColor(healthFor(acc).status)"
                class="font-mono text-xs"
                :title="healthFor(acc).message"
              >
                {{ healthFor(acc).status }}
              </span>
              <span v-else class="text-zinc-600 text-[11px]">—</span>
            </td>

            <!-- Actions -->
            <td class="py-2.5 px-4 text-right">
              <div class="flex items-center justify-end space-x-1">
                <button
                  @click="appStore.checkAccountsHealth([acc.email || acc.username])"
                  :disabled="appStore.checkingHealth"
                  class="p-1 text-zinc-400 hover:text-emerald-400 hover:bg-zinc-800 rounded transition disabled:opacity-50"
                  title="Check IMAP"
                >
                  <AppIcon name="activity" :size="13" />
                </button>
                <button
                  @click="togglePassword(i)"
                  class="p-1 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded transition"
                  :title="showPassword[i] ? 'Hide' : 'Show'"
                >
                  <AppIcon :name="showPassword[i] ? 'lock' : 'eye'" :size="13" />
                </button>
                <button
                  @click="copyCreds(acc)"
                  class="p-1 text-zinc-400 hover:text-indigo-400 hover:bg-zinc-800 rounded transition"
                  title="Copy"
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

function healthTextColor(status) {
  switch (status) {
    case 'active': return 'text-emerald-400'
    case 'password_changed': return 'text-amber-400'
    case 'locked': case 'suspended': return 'text-rose-400'
    default: return 'text-zinc-500'
  }
}
</script>
