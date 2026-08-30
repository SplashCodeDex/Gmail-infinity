"""
Gmail Infinity Factory - Web Dashboard
Modern web interface for managing account creation with real-time monitoring.

Features:
- Beautiful responsive UI with live updates
- Real-time progress tracking via WebSocket
- Interactive configuration management
- Strategy & proxy analytics dashboard
- Account management & export
- Session history & statistics
- Mobile-friendly design
"""
import os
import sys
import json
import time
import asyncio
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Import our core modules
from config.settings import Config
from core.account_manager import account_manager
from core.database import DatabaseManager
from core.proxy_manager import proxy_manager

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'gmail-infinity-secret-key-2026'
app.config['JSON_SORT_KEYS'] = False

# Enable CORS and SocketIO
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state
active_sessions = {}
session_lock = threading.Lock()


class CreationSession:
    """Represents an active account creation session."""

    def __init__(self, session_id: str, config: Dict):
        self.session_id = session_id
        self.config = config
        self.status = 'initializing'  # initializing, running, paused, completed, failed
        self.progress = {
            'current': 0,
            'total': config.get('num_accounts', 0),
            'successes': 0,
            'failures': 0,
            'success_rate': 0.0
        }
        self.created_accounts = []
        self.logs = []
        self.start_time = None
        self.end_time = None
        self.thread = None
        self.stop_flag = False

    def add_log(self, level: str, message: str):
        """Add log entry."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)

        # Emit to connected clients
        socketio.emit('session_log', {
            'session_id': self.session_id,
            'log': log_entry
        })

    def update_progress(self, **kwargs):
        """Update progress metrics."""
        self.progress.update(kwargs)

        # Calculate success rate
        total_attempts = self.progress['successes'] + self.progress['failures']
        if total_attempts > 0:
            self.progress['success_rate'] = (self.progress['successes'] / total_attempts) * 100

        # Emit to connected clients
        socketio.emit('session_progress', {
            'session_id': self.session_id,
            'progress': self.progress
        })

    def add_account(self, account: Dict):
        """Add created account."""
        self.created_accounts.append(account)

        # Emit to connected clients
        socketio.emit('account_created', {
            'session_id': self.session_id,
            'account': account
        })


def run_creation_session(session_id: str):
    """Run account creation in background thread."""
    with session_lock:
        if session_id not in active_sessions:
            return
        session_obj = active_sessions[session_id]

    try:
        session_obj.status = 'running'
        session_obj.start_time = datetime.now()
        session_obj.add_log('info', 'Session started')

        # Import creation logic
        from enhanced_creator import EnhancedCreator

        # Create enhanced creator instance
        config = session_obj.config
        creator = EnhancedCreator(
            num_accounts=config.get('num_accounts', 1),
            use_sms=config.get('use_sms', False),
            use_proxies=config.get('use_proxies', True),
            warmup=config.get('warmup', True),
            export_format=config.get('export_format', 'json'),
            concurrent=config.get('concurrent', 1),
            auto_recover=config.get('auto_recover', True),
            adaptive=config.get('adaptive', True)
        )

        # Hook into creator events
        original_create = creator.create_account_with_intelligence

        def wrapped_create(index, progress=None, task_id=None):
            if session_obj.stop_flag:
                return {'success': False, 'email': 'stopped', 'error': 'Stopped by user'}

            session_obj.add_log('info', f'Creating account {index + 1}/{session_obj.config["num_accounts"]}')
            result = original_create(index, progress, task_id)

            if result['success']:
                session_obj.update_progress(
                    current=index + 1,
                    successes=session_obj.progress['successes'] + 1
                )
                session_obj.add_account(result)
                session_obj.add_log('success', f'✓ Created: {result["email"]}')
            else:
                session_obj.update_progress(
                    current=index + 1,
                    failures=session_obj.progress['failures'] + 1
                )
                session_obj.add_log('error', f'✗ Failed: {result.get("email", "unknown")} - {result.get("error", "Unknown error")}')

            return result

        creator.create_account_with_intelligence = wrapped_create

        # Run creation
        success = creator.run()

        session_obj.status = 'completed' if success else 'failed'
        session_obj.end_time = datetime.now()
        session_obj.add_log('info', f'Session completed: {session_obj.progress["successes"]} successes, {session_obj.progress["failures"]} failures')

        # Emit completion
        socketio.emit('session_complete', {
            'session_id': session_id,
            'status': session_obj.status,
            'progress': session_obj.progress
        })

    except Exception as e:
        session_obj.status = 'failed'
        session_obj.add_log('error', f'Session error: {str(e)}')
        logging.exception(f"Session {session_id} error")


# ============================================================================
# API Routes
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    config = {
        'password_set': bool(Config.YOUR_PASSWORD),
        'sms_providers': {
            'fivesim': bool(Config.FIVESIM_API_KEY),
            'sms_activate': bool(Config.SMS_ACTIVATE_API_KEY),
            'onlinesim': bool(Config.ONLINESIM_API_KEY),
            'getsms': bool(getattr(Config, 'GETSMS_API_KEY', '')),
        },
        'captcha_providers': {
            'twocaptcha': bool(Config.TWOCAPTCHA_API_KEY),
            'anticaptcha': bool(Config.ANTICAPTCHA_API_KEY),
            'capmonster': bool(Config.CAPMONSTER_API_KEY),
        },
        'proxies': {
            'enabled': Config.ENABLE_PROXY,
            'count': proxy_manager.count,
            'healthy': proxy_manager.get_stats().get('healthy', 0),
        },
        'engine': Config.ENGINE_MODE,
        'headless': Config.HEADLESS_MODE,
        'features': {
            'fingerprint_masking': Config.ENABLE_FINGERPRINT_MASKING,
            'human_typing': Config.ENABLE_HUMAN_TYPING_ERRORS,
            'session_warming': Config.ENABLE_SESSION_WARMING,
            'cdp_injection': Config.ENABLE_CDP_INJECTION,
        }
    }
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration."""
    data = request.json

    try:
        # Update Config (Note: This updates in-memory, not .env file)
        if 'headless' in data:
            Config.HEADLESS_MODE = data['headless']
        if 'engine' in data:
            Config.ENGINE_MODE = data['engine']

        return jsonify({'success': True, 'message': 'Configuration updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """Get all created accounts."""
    try:
        accounts = account_manager.get_all()
        return jsonify({
            'success': True,
            'accounts': accounts,
            'count': len(accounts)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/accounts/export', methods=['POST'])
def export_accounts():
    """Export accounts to file."""
    data = request.json
    format_type = data.get('format', 'json')

    try:
        if format_type == 'json':
            path = account_manager.export_json()
        elif format_type == 'csv':
            path = account_manager.export_csv()
        elif format_type == 'txt':
            path = account_manager.export_txt()
        else:
            return jsonify({'success': False, 'error': 'Invalid format'}), 400

        return send_file(path, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/session/start', methods=['POST'])
def start_session():
    """Start new account creation session."""
    data = request.json

    # Validate input
    num_accounts = data.get('num_accounts', 1)
    if num_accounts < 1 or num_accounts > 1000:
        return jsonify({'success': False, 'error': 'Number of accounts must be between 1 and 1000'}), 400

    # Generate session ID
    session_id = f"session_{int(time.time())}_{os.urandom(4).hex()}"

    # Create session object
    session_obj = CreationSession(session_id, data)

    with session_lock:
        active_sessions[session_id] = session_obj

    # Start background thread
    thread = threading.Thread(target=run_creation_session, args=(session_id,))
    thread.daemon = True
    session_obj.thread = thread
    thread.start()

    return jsonify({
        'success': True,
        'session_id': session_id,
        'message': 'Session started'
    })


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details."""
    with session_lock:
        if session_id not in active_sessions:
            return jsonify({'success': False, 'error': 'Session not found'}), 404

        session_obj = active_sessions[session_id]

        return jsonify({
            'success': True,
            'session': {
                'id': session_id,
                'status': session_obj.status,
                'config': session_obj.config,
                'progress': session_obj.progress,
                'start_time': session_obj.start_time.isoformat() if session_obj.start_time else None,
                'end_time': session_obj.end_time.isoformat() if session_obj.end_time else None,
                'accounts_count': len(session_obj.created_accounts),
                'logs_count': len(session_obj.logs)
            }
        })


@app.route('/api/session/<session_id>/stop', methods=['POST'])
def stop_session(session_id):
    """Stop running session."""
    with session_lock:
        if session_id not in active_sessions:
            return jsonify({'success': False, 'error': 'Session not found'}), 404

        session_obj = active_sessions[session_id]
        session_obj.stop_flag = True
        session_obj.status = 'stopped'

        return jsonify({'success': True, 'message': 'Session stopped'})


@app.route('/api/session/<session_id>/logs', methods=['GET'])
def get_session_logs(session_id):
    """Get session logs."""
    with session_lock:
        if session_id not in active_sessions:
            return jsonify({'success': False, 'error': 'Session not found'}), 404

        session_obj = active_sessions[session_id]

        return jsonify({
            'success': True,
            'logs': session_obj.logs[-100:]  # Last 100 logs
        })


@app.route('/api/session/<session_id>/accounts', methods=['GET'])
def get_session_accounts(session_id):
    """Get accounts created in session."""
    with session_lock:
        if session_id not in active_sessions:
            return jsonify({'success': False, 'error': 'Session not found'}), 404

        session_obj = active_sessions[session_id]

        return jsonify({
            'success': True,
            'accounts': session_obj.created_accounts
        })


@app.route('/api/sessions', methods=['GET'])
def get_all_sessions():
    """Get all sessions."""
    with session_lock:
        sessions_data = []
        for session_id, session_obj in active_sessions.items():
            sessions_data.append({
                'id': session_id,
                'status': session_obj.status,
                'progress': session_obj.progress,
                'start_time': session_obj.start_time.isoformat() if session_obj.start_time else None,
                'end_time': session_obj.end_time.isoformat() if session_obj.end_time else None
            })

        return jsonify({
            'success': True,
            'sessions': sessions_data
        })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics."""
    try:
        db = DatabaseManager()

        # Get account stats
        account_stats = account_manager.get_stats()

        # Get proxy stats
        proxy_stats = proxy_manager.get_stats()

        return jsonify({
            'success': True,
            'stats': {
                'accounts': account_stats,
                'proxies': proxy_stats,
                'active_sessions': len([s for s in active_sessions.values() if s.status == 'running'])
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/proxies', methods=['GET'])
def get_proxies():
    """Get proxy information."""
    try:
        proxies = proxy_manager.get_all_proxies()
        stats = proxy_manager.get_stats()

        return jsonify({
            'success': True,
            'proxies': {
                'total': len(proxies),
                'healthy': stats.get('healthy', 0),
                'list': proxies[:10]  # Show first 10 for security
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/proxies/test', methods=['POST'])
def test_proxies():
    """Test proxy health."""
    try:
        results = proxy_manager.check_all_health()
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# WebSocket Events
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('connected', {'message': 'Connected to Gmail Infinity Factory'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    pass


@socketio.on('subscribe_session')
def handle_subscribe(data):
    """Subscribe to session updates."""
    session_id = data.get('session_id')
    if session_id:
        # Client will receive updates for this session
        emit('subscribed', {'session_id': session_id})


# ============================================================================
# Main
# ============================================================================

def create_templates():
    """Create template directory and files if they don't exist."""
    template_dir = Path(__file__).parent / 'templates'
    template_dir.mkdir(exist_ok=True)

    dashboard_html = template_dir / 'dashboard.html'

    if not dashboard_html.exists():
        with open(dashboard_html, 'w', encoding='utf-8') as f:
            f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gmail Infinity Factory - Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-900 text-gray-100">
    <!-- Dashboard content will be loaded here -->
    <div id="app" class="min-h-screen">
        <h1 class="text-center text-4xl font-bold py-8">Loading Dashboard...</h1>
    </div>

    <script>
        // Dashboard will be implemented in next file
        document.getElementById('app').innerHTML = '<div class="container mx-auto p-8"><h1 class="text-4xl font-bold mb-4">Gmail Infinity Factory</h1><p>Dashboard UI loading...</p></div>';
    </script>
</body>
</html>''')


def main():
    """Start web dashboard."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Create templates
    create_templates()

    # Create data directory
    os.makedirs('data', exist_ok=True)

    # Print startup info
    print("=" * 80)
    print("  GMAIL INFINITY FACTORY - WEB DASHBOARD")
    print("=" * 80)
    print()
    print("  🌐 Dashboard URL: http://localhost:5000")
    print("  📊 Real-time monitoring with WebSocket")
    print("  🚀 Enhanced intelligence engine integrated")
    print()
    print("  Press Ctrl+C to stop the server")
    print("=" * 80)
    print()

    # Start Flask-SocketIO server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()
