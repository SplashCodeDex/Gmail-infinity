/**
 * Gmail Infinity - Centralized UI & Application Configuration
 */

export const WORKER_OPTIONS = [
  { label: '1 Worker', value: 1 },
  { label: '2 Workers', value: 2 },
  { label: '3 Workers', value: 3 },
  { label: '5 Workers', value: 5 },
]

export const EXPORT_FORMATS = [
  { label: 'JSON Document (.json)', value: 'json', mimeType: 'application/json' },
  { label: 'CSV Spreadsheet (.csv)', value: 'csv', mimeType: 'text/csv' },
  { label: 'Plain Text (.txt)', value: 'txt', mimeType: 'text/plain' },
  { label: 'All Formats (.zip)', value: 'all', mimeType: 'application/octet-stream' },
]

export const CREATION_FLOWS = [
  {
    id: 'adaptive',
    name: 'Adaptive AI',
    description: 'Thompson Sampling route optimizer',
  },
  {
    id: 'standard',
    name: 'Standard Direct',
    description: 'Direct Google account creation',
  },
  {
    id: 'youtube',
    name: 'YouTube Route',
    description: 'Consumer onboarding path',
  },
  {
    id: 'workspace',
    name: 'Google Workspace',
    description: 'Enterprise entry point',
  },
]

export const DEFAULT_SESSION_CONFIG = {
  num_accounts: 5,
  concurrent: 1,
  use_sms: false,
  use_proxies: true,
  warmup: true,
  flow_mode: 'adaptive',
  adaptive: true,
  export_format: 'json',
  auto_recover: true,
}

export const SESSION_STATUS_STYLES = {
  running: {
    badge: 'bg-zinc-800 text-emerald-400 border border-zinc-700',
    label: 'Running',
  },
  completed: {
    badge: 'bg-zinc-800 text-zinc-300 border border-zinc-700',
    label: 'Completed',
  },
  failed: {
    badge: 'bg-zinc-800 text-rose-400 border border-zinc-700',
    label: 'Failed',
  },
  stopped: {
    badge: 'bg-zinc-800 text-amber-400 border border-zinc-700',
    label: 'Stopped',
  },
  initializing: {
    badge: 'bg-zinc-800 text-zinc-400 border border-zinc-700',
    label: 'Initializing',
  },
}

export const LOG_LEVELS = [
  { id: 'all', label: 'All' },
  { id: 'info', label: 'Info' },
  { id: 'success', label: 'Success' },
  { id: 'warning', label: 'Warnings' },
  { id: 'error', label: 'Errors' },
]

export const LOG_STYLES = {
  info: {
    text: 'text-zinc-300',
  },
  success: {
    text: 'text-emerald-400',
  },
  warning: {
    text: 'text-amber-400',
  },
  error: {
    text: 'text-rose-400',
  },
}

export const NAV_TABS = [
  { id: 'overview', label: 'Overview', icon: 'activity' },
  { id: 'accounts', label: 'Accounts', icon: 'database' },
  { id: 'proxies', label: 'Proxies', icon: 'shield' },
  { id: 'diagnostics', label: 'Engine', icon: 'cpu' },
]

export const APP_CONFIG = {
  name: 'Gmail Infinity',
  version: '2.0.0',
  tagline: 'Autonomous Provisioning Suite',
  refreshIntervalMs: 4000,
  maxLogHistory: 300,
}


