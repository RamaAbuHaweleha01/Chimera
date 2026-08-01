"""
Chimera - Screenshot Module
Captures desktop screenshots
"""
import os
import base64
import io
from PIL import ImageGrab
import time
import threading

class Screenshot:
    def __init__(self):
        self.screenshots = []
        self.running = False
    
    def capture(self):
        """Capture a single screenshot and return base64"""
        try:
            screenshot = ImageGrab.grab(all_screens=True)
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return {
                "timestamp": time.time(),
                "data": img_base64,
                "size": len(buffered.getvalue())
            }
        except Exception as e:
            return None
    
    def capture_and_get(self):
        """Capture screenshot and return immediately"""
        return self.capture()
    
    def stop(self):
        """Stop capture thread"""
        self.running = False
