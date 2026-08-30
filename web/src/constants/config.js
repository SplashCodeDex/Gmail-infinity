/**
 * Gmail Infinity - Centralized UI & Application Configuration
 * Eliminates all magic strings, hardcoded options, and scattered color definitions.
 */

export const WORKER_OPTIONS = [
  { label: '1 Worker (Safe & Steady)', value: 1, description: 'Single worker with humanized delay profiles' },
  { label: '2 Workers (Balanced)', value: 2, description: 'Dual parallel execution with low detection footprint' },
  { label: '3 Workers (Fast Batch)', value: 3, description: 'High throughput creation mode' },
  { label: '5 Workers (Maximum Turbo)', value: 5, description: 'Maximum concurrency utilizing multi-core workers' },
]

export const EXPORT_FORMATS = [
  { label: 'JSON Document (.json)', value: 'json', mimeType: 'application/json' },
  { label: 'CSV Spreadsheet (.csv)', value: 'csv', mimeType: 'text/csv' },
  { label: 'Plain Text (.txt)', value: 'txt', mimeType: 'text/plain' },
  { label: 'All Formats (.zip / archive)', value: 'all', mimeType: 'application/octet-stream' },
]

export const ENGINE_MODES = [
  { id: 'playwright', label: 'Playwright (Stealth Web)', badge: 'Default', description: 'Deep anti-bot browser automation with CDP masking' },
  { id: 'selenium', label: 'Selenium (Undetected Driver)', badge: 'Alternative', description: 'Patched chromedriver with native stealth hooks' },
  { id: 'appium', label: 'Appium (Android Native OS)', badge: 'Bypass Phone', description: 'Creates account inside Android Settings (Zero Phone Trigger)' },
]

export const IDENTITY_NAME_OPTIONS = [
  { id: 'standard', label: 'Western / Standard Names', description: 'Diverse realistic US/EU identity pool' },
  { id: 'arabic', label: 'Arabic / Middle Eastern', description: 'Middle Eastern localized name sets' },
]

export const DEFAULT_SESSION_CONFIG = {
  num_accounts: 5,
  concurrent: 1,
  use_sms: false,
  use_proxies: true,
  warmup: true,
  adaptive: true,
  export_format: 'json',
  auto_recover: true,
  engine_mode: 'playwright',
  use_arabic_names: false,
  enable_poltergeist: true,
  enable_cookie_reaper: true,
  enable_recovery_chain: true,
}


export const SESSION_PRESETS = [
  {
    id: 'stealth',
    name: 'Stealth & Safety',
    description: '1 worker, warmup enabled, proxy rotation, adaptive AI anti-bot',
    config: { num_accounts: 3, concurrent: 1, use_sms: false, use_proxies: true, warmup: true, adaptive: true },
  },
  {
    id: 'standard',
    name: 'Standard Production',
    description: '2 workers, adaptive fingerprints, automatic recovery',
    config: { num_accounts: 10, concurrent: 2, use_sms: false, use_proxies: true, warmup: true, adaptive: true },
  },
  {
    id: 'turbo',
    name: 'High Throughput Turbo',
    description: '3 workers, high concurrency, fast generation',
    config: { num_accounts: 25, concurrent: 3, use_sms: false, use_proxies: true, warmup: false, adaptive: true },
  },
]

export const SESSION_STATUS_STYLES = {
  running: {
    badge: 'bg-emerald-950 text-emerald-300 border border-emerald-800',
    indicator: 'bg-emerald-500',
    label: 'Running',
    pulse: true,
  },
  completed: {
    badge: 'bg-indigo-950 text-indigo-300 border border-indigo-800',
    indicator: 'bg-indigo-500',
    label: 'Completed',
    pulse: false,
  },
  failed: {
    badge: 'bg-rose-950 text-rose-300 border border-rose-800',
    indicator: 'bg-rose-500',
    label: 'Failed',
    pulse: false,
  },
  stopped: {
    badge: 'bg-amber-950 text-amber-300 border border-amber-800',
    indicator: 'bg-amber-500',
    label: 'Stopped',
    pulse: false,
  },
  initializing: {
    badge: 'bg-purple-950 text-purple-300 border border-purple-800',
    indicator: 'bg-purple-500',
    label: 'Initializing',
    pulse: true,
  },
}

export const LOG_LEVELS = [
  { id: 'all', label: 'All Logs' },
  { id: 'info', label: 'Info' },
  { id: 'success', label: 'Success' },
  { id: 'warning', label: 'Warnings' },
  { id: 'error', label: 'Errors' },
]

export const LOG_STYLES = {
  info: {
    text: 'text-zinc-300',
    badge: 'bg-zinc-800 text-zinc-300 border border-zinc-700',
    iconColor: 'text-cyan-400',
    icon: 'info',
  },
  success: {
    text: 'text-emerald-300',
    badge: 'bg-emerald-950 text-emerald-300 border border-emerald-800',
    iconColor: 'text-emerald-400',
    icon: 'check-circle',
  },
  warning: {
    text: 'text-amber-300',
    badge: 'bg-amber-950 text-amber-300 border border-amber-800',
    iconColor: 'text-amber-400',
    icon: 'alert-triangle',
  },
  error: {
    text: 'text-rose-400 font-semibold',
    badge: 'bg-rose-950 text-rose-300 border border-rose-800',
    iconColor: 'text-rose-400',
    icon: 'x-circle',
  },
}

export const NAV_TABS = [
  { id: 'overview', label: 'Overview', icon: 'activity' },
  { id: 'accounts', label: 'Accounts', icon: 'database' },
  { id: 'proxies', label: 'Proxies', icon: 'shield' },
  { id: 'terminal', label: 'Terminal', icon: 'terminal' },
  { id: 'diagnostics', label: 'Engine', icon: 'cpu' },
]

export const APP_CONFIG = {
  name: 'Gmail Infinity',
  version: '2.0.0',
  tagline: 'Autonomous Provisioning Suite',
  refreshIntervalMs: 4000,
  maxLogHistory: 300,
}

