/**
 * Gmail Infinity Factory - Unified Full-Stack Dev Server Runner
 * Runs FastAPI backend and Vite frontend concurrently with unified logging and graceful shutdown.
 */
import { spawn } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '..')
const webDir = path.resolve(rootDir, 'web')

const colors = {
  reset: '\x1b[0m',
  cyan: '\x1b[36m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  bold: '\x1b[1m',
}

console.log(`${colors.bold}${colors.cyan}╔══════════════════════════════════════════════════════════╗${colors.reset}`)
console.log(`${colors.bold}${colors.cyan}║   GMAIL INFINITY FACTORY - UNIFIED DEV STACK LAUNCHER   ║${colors.reset}`)
console.log(`${colors.bold}${colors.cyan}╚══════════════════════════════════════════════════════════╝${colors.reset}`)
console.log(`${colors.yellow}→ Starting FastAPI Backend on http://localhost:8000 ...${colors.reset}`)
console.log(`${colors.yellow}→ Starting Vite Frontend on http://localhost:3000 ...${colors.reset}\n`)

const isWindows = process.platform === 'win32'
const pythonCmd = isWindows ? 'python' : 'python3'
const npmCmd = isWindows ? 'npm.cmd' : 'npm'

// 1. Launch FastAPI Backend
const apiProcess = spawn(pythonCmd, ['api/main.py'], {
  cwd: rootDir,
  shell: false,
  env: { ...process.env, PYTHONUNBUFFERED: '1' }
})

apiProcess.stdout.on('data', (data) => {
  const lines = data.toString().split('\n')
  for (const line of lines) {
    if (line.trim()) {
      console.log(`${colors.cyan}[API]${colors.reset} ${line}`)
    }
  }
})

apiProcess.stderr.on('data', (data) => {
  const lines = data.toString().split('\n')
  for (const line of lines) {
    if (line.trim()) {
      console.error(`${colors.cyan}[API]${colors.reset} ${line}`)
    }
  }
})

// 2. Launch Vite Frontend
const webProcess = spawn(npmCmd, ['run', 'dev'], {
  cwd: webDir,
  shell: false,
})

webProcess.stdout.on('data', (data) => {
  const lines = data.toString().split('\n')
  for (const line of lines) {
    if (line.trim()) {
      console.log(`${colors.green}[WEB]${colors.reset} ${line}`)
    }
  }
})

webProcess.stderr.on('data', (data) => {
  const lines = data.toString().split('\n')
  for (const line of lines) {
    if (line.trim()) {
      console.error(`${colors.green}[WEB]${colors.reset} ${line}`)
    }
  }
})

// Handle clean process shutdown
function cleanup() {
  console.log(`\n${colors.yellow}Shutting down FastAPI and Vite servers...${colors.reset}`)
  try {
    if (isWindows) {
      if (apiProcess.pid) spawn('taskkill', ['/pid', String(apiProcess.pid), '/f', '/t'], { shell: false })
      if (webProcess.pid) spawn('taskkill', ['/pid', String(webProcess.pid), '/f', '/t'], { shell: false })
    } else {
      apiProcess.kill('SIGTERM')
      webProcess.kill('SIGTERM')
    }
  } catch (e) {
    // Ignore cleanup errors
  }
  process.exit(0)
}

process.on('SIGINT', cleanup)
process.on('SIGTERM', cleanup)
