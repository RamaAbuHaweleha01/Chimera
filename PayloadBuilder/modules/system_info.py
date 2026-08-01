"""
Chimera - System Information Collector
Collects: OS, CPU, RAM, Disk, Network, Users
"""
import platform
import socket
import psutil
import os
import json
import uuid
import subprocess

class SystemInfo:
    @staticmethod
    def collect():
        info = {
            "device_id": SystemInfo._get_device_id(),
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "cpu_cores": psutil.cpu_count(),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory": SystemInfo._get_memory(),
            "disks": SystemInfo._get_disks(),
            "network": SystemInfo._get_network(),
            "users": SystemInfo._get_users(),
            "uptime": SystemInfo._get_uptime(),
            "ip": SystemInfo._get_ip()
        }
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
            "total": round(mem.total / (1024**3), 2),
            "available": round(mem.available / (1024**3), 2),
            "used": round(mem.used / (1024**3), 2),
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
                    "total": round(usage.total / (1024**3), 2),
                    "used": round(usage.used / (1024**3), 2),
                    "free": round(usage.free / (1024**3), 2),
                    "percent": usage.percent
                })
            except:
                continue
        return disks
    
    @staticmethod
    def _get_network():
        interfaces = []
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    interfaces.append({
                        "name": name,
                        "ip": addr.address
                    })
        return interfaces
    
    @staticmethod
    def _get_users():
        users = []
        for user in psutil.users():
            users.append({
                "name": user.name,
                "host": user.host,
                "started": user.started
            })
        return users
    
    @staticmethod
    def _get_uptime():
        try:
            return psutil.boot_time()
        except:
            return None
    
    @staticmethod
    def _get_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
