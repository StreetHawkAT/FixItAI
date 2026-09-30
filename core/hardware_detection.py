import platform
import subprocess
import psutil

def detect_hardware():
    arch = platform.machine().lower()
    is_arm = 'arm' in arch or 'aarch64' in arch
    
    processor = "Unknown"
    try:
        output = subprocess.check_output(
            ["powershell", "-Command", "(Get-WmiObject Win32_Processor).Name"],
            text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        if output:
            processor = output.strip()
    except:
        pass
        
    is_snapdragon = "snapdragon" in processor.lower()
    
    # OS Info
    os_info = f"{platform.system()} {platform.release()}"
    
    # Memory Info
    mem = psutil.virtual_memory()
    total_memory_gb = round(mem.total / (1024 ** 3), 1)
    
    npu_available = is_snapdragon
    
    return {
        "os": os_info,
        "architecture": "ARM64" if is_arm else "x64" if "amd64" in arch else arch,
        "processor": processor,
        "memory_gb": total_memory_gb,
        "is_snapdragon": is_snapdragon,
        "ai_acceleration": "Available (Snapdragon NPU)" if npu_available else "Not detected",
        "npu_available": npu_available
    }
