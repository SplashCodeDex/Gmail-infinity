// Gmail Infinity Factory - Dashboard JavaScript
let socket;
let currentSessions = {};
let recentAccounts = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeWebSocket();
    loadInitialData();
    setupEventListeners();
});

// WebSocket Connection
function initializeWebSocket() {
    socket = io();

    socket.on('connect', function() {
        console.log('Connected to server');
        updateConnectionStatus(true);
    });

    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
    });

    socket.on('session_progress', function(data) {
        updateSessionProgress(data.session_id, data.progress);
    });

    socket.on('session_log', function(data) {
        addLogEntry(data.log);
    });

    socket.on('account_created', function(data) {
        addRecentAccount(data.account);
    });

    socket.on('session_complete', function(data) {
        handleSessionComplete(data.session_id, data.status);
    });
}

// Update connection status indicator
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    if (connected) {
        statusEl.innerHTML = `
            <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span class="text-sm text-white">Connected</span>
        `;
    } else {
        statusEl.innerHTML = `
            <div class="w-3 h-3 bg-red-500 rounded-full"></div>
            <span class="text-sm text-white">Disconnected</span>
        `;
    }
}

// Load initial data
async function loadInitialData() {
    try {
        // Load statistics
        const statsRes = await fetch('/api/stats');
        const statsData = await statsRes.json();
        if (statsData.success) {
            updateStatistics(statsData.stats);
        }

        // Load active sessions
        const sessionsRes = await fetch('/api/sessions');
        const sessionsData = await sessionsRes.json();
        if (sessionsData.success) {
            updateSessionsList(sessionsData.sessions);
        }

        // Load accounts
        const accountsRes = await fetch('/api/accounts');
        const accountsData = await accountsRes.json();
        if (accountsData.success) {
            recentAccounts = accountsData.accounts.slice(-10).reverse();
            updateRecentAccountsTable();
        }
    } catch (error) {
        console.error('Error loading initial data:', error);
    }
}

// Update statistics cards
function updateStatistics(stats) {
    document.getElementById('totalAccounts').textContent = stats.accounts?.total || 0;

    const successRate = stats.accounts?.success_rate || 0;
    document.getElementById('successRate').textContent = successRate.toFixed(1) + '%';

    document.getElementById('activeProxies').textContent = stats.proxies?.healthy || 0;
    document.getElementById('activeSessions').textContent = stats.active_sessions || 0;
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('createSessionForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await createNewSession();
    });
}

// Create new session
async function createNewSession() {
    const formData = {
        num_accounts: parseInt(document.getElementById('numAccounts').value),
        concurrent: parseInt(document.getElementById('concurrent').value),
        use_sms: document.getElementById('useSms').checked,
        use_proxies: document.getElementById('useProxies').checked,
        warmup: document.getElementById('warmup').checked,
        adaptive: document.getElementById('adaptive').checked,
        export_format: document.getElementById('exportFormat').value,
        auto_recover: true
    };

    try {
        const response = await fetch('/api/session/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Session started successfully!', 'success');
            addLogEntry({
                timestamp: new Date().toISOString(),
                level: 'info',
                message: `New session started: ${data.session_id}`
            });

            // Subscribe to session updates
            socket.emit('subscribe_session', { session_id: data.session_id });

            // Reload sessions list
            setTimeout(loadInitialData, 1000);
        } else {
            showNotification('Failed to start session: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error starting session:', error);
        showNotification('Error starting session', 'error');
    }
}

// Update sessions list
function updateSessionsList(sessions) {
    const container = document.getElementById('sessionsContainer');

    if (!sessions || sessions.length === 0) {
        container.innerHTML = '<p class="text-gray-400 text-center py-8">No active sessions</p>';
        return;
    }

    container.innerHTML = sessions.map(session => {
        const statusColor = {
            'running': 'green',
            'completed': 'blue',
            'failed': 'red',
            'stopped': 'yellow',
            'initializing': 'purple'
        }[session.status] || 'gray';

        const progressPercent = session.progress.total > 0
            ? (session.progress.current / session.progress.total * 100).toFixed(1)
            : 0;

        return `
            <div class="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-3">
                        <div class="w-3 h-3 bg-${statusColor}-500 rounded-full ${session.status === 'running' ? 'animate-pulse' : ''}"></div>
                        <span class="font-mono text-sm text-gray-400">${session.id}</span>
                    </div>
                    <span class="px-3 py-1 bg-${statusColor}-500/20 text-${statusColor}-400 rounded-full text-xs font-semibold uppercase">
                        ${session.status}
                    </span>
                </div>

                <div class="mb-3">
                    <div class="flex justify-between text-sm mb-1">
                        <span class="text-gray-400">Progress</span>
                        <span class="text-white font-semibold">${session.progress.current}/${session.progress.total}</span>
                    </div>
                    <div class="w-full bg-gray-600 rounded-full h-2">
                        <div class="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all duration-500" style="width: ${progressPercent}%"></div>
                    </div>
                </div>

                <div class="grid grid-cols-3 gap-2 text-xs">
                    <div class="text-center p-2 bg-green-500/10 rounded">
                        <div class="text-green-400 font-bold">${session.progress.successes}</div>
                        <div class="text-gray-400">Success</div>
                    </div>
                    <div class="text-center p-2 bg-red-500/10 rounded">
                        <div class="text-red-400 font-bold">${session.progress.failures}</div>
                        <div class="text-gray-400">Failed</div>
                    </div>
                    <div class="text-center p-2 bg-blue-500/10 rounded">
                        <div class="text-blue-400 font-bold">${session.progress.success_rate.toFixed(1)}%</div>
                        <div class="text-gray-400">Rate</div>
                    </div>
                </div>

                ${session.status === 'running' ? `
                    <button onclick="stopSession('${session.id}')" class="w-full mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-white text-sm transition">
                        <i class="fas fa-stop mr-2"></i>Stop Session
                    </button>
                ` : ''}
            </div>
        `;
    }).join('');

    // Store current sessions
    sessions.forEach(session => {
        currentSessions[session.id] = session;
    });
}

// Update session progress
function updateSessionProgress(sessionId, progress) {
    if (currentSessions[sessionId]) {
        currentSessions[sessionId].progress = progress;
        loadInitialData(); // Refresh display
    }
}

// Stop session
async function stopSession(sessionId) {
    if (!confirm('Are you sure you want to stop this session?')) {
        return;
    }

    try {
        const response = await fetch(`/api/session/${sessionId}/stop`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Session stopped', 'success');
            loadInitialData();
        } else {
            showNotification('Failed to stop session', 'error');
        }
    } catch (error) {
        console.error('Error stopping session:', error);
        showNotification('Error stopping session', 'error');
    }
}

// Handle session completion
function handleSessionComplete(sessionId, status) {
    showNotification(`Session ${sessionId} completed with status: ${status}`,
        status === 'completed' ? 'success' : 'warning');
    loadInitialData();
}

// Add log entry
function addLogEntry(log) {
    const container = document.getElementById('logsContainer');

    const levelColors = {
        'info': 'text-blue-400',
        'success': 'text-green-400',
        'warning': 'text-yellow-400',
        'error': 'text-red-400'
    };

    const levelIcons = {
        'info': 'fa-info-circle',
        'success': 'fa-check-circle',
        'warning': 'fa-exclamation-triangle',
        'error': 'fa-times-circle'
    };

    const time = new Date(log.timestamp).toLocaleTimeString();
    const levelClass = levelColors[log.level] || 'text-gray-400';
    const levelIcon = levelIcons[log.level] || 'fa-circle';

    const logEntry = document.createElement('div');
    logEntry.className = 'mb-2 flex items-start space-x-2';
    logEntry.innerHTML = `
        <span class="text-gray-500">[${time}]</span>
        <i class="fas ${levelIcon} ${levelClass} mt-1"></i>
        <span class="${levelClass}">${log.message}</span>
    `;

    // Remove "waiting" message if present
    if (container.querySelector('.text-gray-500')) {
        container.innerHTML = '';
    }

    container.appendChild(logEntry);
    container.scrollTop = container.scrollHeight;

    // Keep only last 100 logs
    while (container.children.length > 100) {
        container.removeChild(container.firstChild);
    }
}

// Add recent account
function addRecentAccount(account) {
    recentAccounts.unshift(account);
    if (recentAccounts.length > 10) {
        recentAccounts.pop();
    }
    updateRecentAccountsTable();
}

// Update recent accounts table
function updateRecentAccountsTable() {
    const tbody = document.getElementById('recentAccountsTable');

    if (!recentAccounts || recentAccounts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center text-gray-500 py-4">No accounts created yet</td></tr>';
        return;
    }

    tbody.innerHTML = recentAccounts.map(account => {
        const time = account.created_at ? new Date(account.created_at).toLocaleTimeString() : 'Unknown';
        return `
            <tr class="border-b border-gray-700 hover:bg-gray-700/50 transition">
                <td class="py-2 text-green-400 font-mono text-sm">${account.email}</td>
                <td class="py-2 text-yellow-400 font-mono text-sm">${account.password}</td>
                <td class="py-2 text-gray-400 text-sm">${time}</td>
            </tr>
        `;
    }).join('');
}

// Test proxies
async function testProxies() {
    showNotification('Testing proxies...', 'info');

    try {
        const response = await fetch('/api/proxies/test', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`Proxy test complete: ${data.results.healthy} healthy`, 'success');
            loadInitialData();
        } else {
            showNotification('Proxy test failed', 'error');
        }
    } catch (error) {
        console.error('Error testing proxies:', error);
        showNotification('Error testing proxies', 'error');
    }
}

// Show all accounts (in modal or new page)
async function showAccounts() {
    try {
        const response = await fetch('/api/accounts');
        const data = await response.json();

        if (data.success) {
            // For now, just show count
            showNotification(`Total accounts: ${data.count}`, 'info');
            // TODO: Implement modal or dedicated page
        }
    } catch (error) {
        console.error('Error loading accounts:', error);
        showNotification('Error loading accounts', 'error');
    }
}

// Export all accounts
async function exportAllAccounts() {
    const format = document.getElementById('exportFormat').value;

    try {
        const response = await fetch('/api/accounts/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ format: format })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `accounts_${Date.now()}.${format}`;
            a.click();
            showNotification('Accounts exported successfully', 'success');
        } else {
            showNotification('Export failed', 'error');
        }
    } catch (error) {
        console.error('Error exporting accounts:', error);
        showNotification('Error exporting accounts', 'error');
    }
}

// Show notification
function showNotification(message, type) {
    // Simple console log for now
    console.log(`[${type.toUpperCase()}] ${message}`);

    // Add to logs
    addLogEntry({
        timestamp: new Date().toISOString(),
        level: type === 'error' ? 'error' : type === 'success' ? 'success' : 'info',
        message: message
    });
}

// Auto-refresh stats every 5 seconds
setInterval(() => {
    if (socket && socket.connected) {
        loadInitialData();
    }
}, 5000);
