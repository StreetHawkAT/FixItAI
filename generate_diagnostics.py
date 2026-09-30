import os

base_dir = r"c:\Users\aksha\OneDrive\Desktop\college\Hackthon\Fixit_ai\diagnostics"
os.makedirs(base_dir, exist_ok=True)

# Helper for PowerShell execution (will be in a shared utils or each file)
# Since we have run_ps in network.py, let's just copy a robust run_ps in each or use a shared one.
# For simplicity, I'll put run_ps in each to be self-contained as requested by previous architecture.

shared_header = '''import subprocess
import json

def run_ps(cmd):
    try:
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.stdout.strip()
    except Exception as e:
        return ""

def parse_json(data):
    if not data: return []
    try:
        parsed = json.loads(data)
        if isinstance(parsed, dict): return [parsed]
        if isinstance(parsed, list): return parsed
    except:
        pass
    return []
'''

modules = {
    "audio.py": '''
def check_audio():
    evidence = []
    
    # Check services
    audiosrv = run_ps("(Get-Service -Name AudioSrv -ErrorAction SilentlyContinue).Status")
    audioendpoint = run_ps("(Get-Service -Name AudioEndpointBuilder -ErrorAction SilentlyContinue).Status")
    
    # Check audio devices
    devices = parse_json(run_ps("Get-PnpDevice -Class Media -ErrorAction SilentlyContinue | Select-Object Name, Status, Present | ConvertTo-Json -Compress"))
    
    if audiosrv.lower() != "running":
        evidence.append("Windows Audio Service (AudioSrv) is stopped.")
    if audioendpoint.lower() != "running":
        evidence.append("Windows Audio Endpoint Builder Service is stopped.")
        
    device_error = False
    device_present = len(devices) > 0
    device_enabled = False
    
    for d in devices:
        status = str(d.get("Status", "")).upper()
        if status == "ERROR": device_error = True
        elif status == "OK": device_enabled = True
        evidence.append(f"Device: {d.get('Name')} | Status: {status}")
        
    if not device_present:
        evidence.append("No audio media devices detected.")
        
    status = "healthy"
    if audiosrv.lower() != "running" or audioendpoint.lower() != "running":
        status = "problem"
    elif not device_present or device_error:
        status = "problem"
        
    return {
        "category": "audio",
        "status": status,
        "service_running": (audiosrv.lower() == "running"),
        "endpoint_service": (audioendpoint.lower() == "running"),
        "output_device_present": device_present,
        "device_enabled": device_enabled,
        "driver_status": "error" if device_error else "ok",
        "evidence": evidence
    }
''',

    "bluetooth.py": '''
def check_bluetooth():
    evidence = []
    
    bthserv = run_ps("(Get-Service -Name bthserv -ErrorAction SilentlyContinue).Status")
    
    devices = parse_json(run_ps("Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | Select-Object Name, Status, Present | ConvertTo-Json -Compress"))
    
    if bthserv.lower() != "running":
        evidence.append("Bluetooth Support Service is stopped.")
        
    device_error = False
    adapter_present = False
    adapter_enabled = False
    
    for d in devices:
        name = str(d.get("Name", "")).lower()
        status = str(d.get("Status", "")).upper()
        if "enumerator" not in name:
            adapter_present = True
            if status == "ERROR": device_error = True
            elif status == "OK": adapter_enabled = True
        evidence.append(f"BT Device: {d.get('Name')} | Status: {status}")
        
    if not adapter_present:
        evidence.append("No main Bluetooth adapter detected.")
        
    status = "healthy"
    if bthserv.lower() != "running":
        status = "problem"
    elif not adapter_present or device_error:
        status = "problem"
        
    return {
        "category": "bluetooth",
        "status": status,
        "service_running": (bthserv.lower() == "running"),
        "bluetooth_present": adapter_present,
        "driver_status": "error" if device_error else "ok",
        "evidence": evidence
    }
''',

    "display.py": '''
def check_display():
    evidence = []
    
    gpus = parse_json(run_ps("Get-PnpDevice -Class Display -ErrorAction SilentlyContinue | Select-Object Name, Status, Present | ConvertTo-Json -Compress"))
    monitors = parse_json(run_ps("Get-PnpDevice -Class Monitor -ErrorAction SilentlyContinue | Select-Object Name, Status, Present | ConvertTo-Json -Compress"))
    
    gpu_error = False
    gpu_present = len(gpus) > 0
    
    for g in gpus:
        status = str(g.get("Status", "")).upper()
        if status == "ERROR": gpu_error = True
        evidence.append(f"GPU: {g.get('Name')} | Status: {status}")
        
    for m in monitors:
        status = str(m.get("Status", "")).upper()
        evidence.append(f"Monitor: {m.get('Name')} | Status: {status}")
        
    if not gpu_present:
        evidence.append("No display adapter (GPU) detected.")
    if len(monitors) == 0:
        evidence.append("No monitors detected by PnP.")
        
    status = "healthy"
    if gpu_error or not gpu_present:
        status = "problem"
    elif len(monitors) == 0:
        status = "problem"
        
    return {
        "category": "display",
        "status": status,
        "gpu_present": gpu_present,
        "driver_status": "error" if gpu_error else "ok",
        "monitors_detected": len(monitors),
        "evidence": evidence
    }
''',

    "keyboard.py": '''
def check_keyboard():
    evidence = []
    
    keyboards = parse_json(run_ps("Get-PnpDevice -Class Keyboard -ErrorAction SilentlyContinue | Select-Object Name, Status, Present | ConvertTo-Json -Compress"))
    
    kb_error = False
    kb_present = len(keyboards) > 0
    
    for k in keyboards:
        status = str(k.get("Status", "")).upper()
        if status == "ERROR": kb_error = True
        evidence.append(f"Keyboard: {k.get('Name')} | Status: {status}")
        
    status = "healthy"
    if kb_error or not kb_present:
        status = "problem"
        
    return {
        "category": "keyboard",
        "status": status,
        "keyboard_present": kb_present,
        "driver_status": "error" if kb_error else "ok",
        "evidence": evidence
    }
''',

    "input_devices.py": '''
def check_input():
    evidence = []
    
    mice = parse_json(run_ps("Get-PnpDevice -Class Mouse -ErrorAction SilentlyContinue | Select-Object Name, Status, Present | ConvertTo-Json -Compress"))
    
    mouse_error = False
    mouse_present = len(mice) > 0
    
    for m in mice:
        status = str(m.get("Status", "")).upper()
        if status == "ERROR": mouse_error = True
        evidence.append(f"Mouse/Touchpad: {m.get('Name')} | Status: {status}")
        
    status = "healthy"
    if mouse_error or not mouse_present:
        status = "problem"
        
    return {
        "category": "mouse_touchpad",
        "status": status,
        "mouse_present": mouse_present,
        "driver_status": "error" if mouse_error else "ok",
        "evidence": evidence
    }
''',

    "microphone.py": '''
def check_microphone():
    # AudioEndpoint checks are complex, we rely on Audio Media class
    evidence = []
    
    audiosrv = run_ps("(Get-Service -Name AudioSrv -ErrorAction SilentlyContinue).Status")
    devices = parse_json(run_ps("Get-PnpDevice -Class Media -ErrorAction SilentlyContinue | Select-Object Name, Status, Present | ConvertTo-Json -Compress"))
    
    device_error = False
    device_present = len(devices) > 0
    
    for d in devices:
        status = str(d.get("Status", "")).upper()
        if status == "ERROR": device_error = True
        evidence.append(f"Audio Device: {d.get('Name')} | Status: {status}")
        
    if audiosrv.lower() != "running":
        evidence.append("Windows Audio Service is stopped (affects microphones).")
        
    status = "healthy"
    if audiosrv.lower() != "running" or not device_present or device_error:
        status = "problem"
        
    return {
        "category": "microphone",
        "status": status,
        "microphone_present": device_present,
        "driver_status": "error" if device_error else "ok",
        "service_running": (audiosrv.lower() == "running"),
        "evidence": evidence
    }
''',

    "usb.py": '''
def check_usb():
    evidence = []
    
    usbs = parse_json(run_ps("Get-PnpDevice -Class USB -ErrorAction SilentlyContinue | Select-Object Name, Status, Present | ConvertTo-Json -Compress"))
    
    usb_error = False
    error_devices = []
    
    for u in usbs:
        status = str(u.get("Status", "")).upper()
        if status == "ERROR": 
            usb_error = True
            error_devices.append(u.get('Name'))
            evidence.append(f"USB Error: {u.get('Name')} | Status: {status}")
            
    if not usbs:
        evidence.append("No USB controllers/devices detected.")
    elif not usb_error:
        evidence.append(f"Detected {len(usbs)} USB devices/controllers functioning normally.")
        
    status = "healthy"
    if usb_error:
        status = "problem"
        
    return {
        "category": "usb",
        "status": status,
        "usb_error": usb_error,
        "error_devices": error_devices,
        "evidence": evidence
    }
''',

    "printer.py": '''
def check_printer():
    evidence = []
    
    spooler = run_ps("(Get-Service -Name Spooler -ErrorAction SilentlyContinue).Status")
    printers = parse_json(run_ps("Get-Printer | Select-Object Name, PrinterStatus | ConvertTo-Json -Compress"))
    
    if spooler.lower() != "running":
        evidence.append("Print Spooler Service is stopped.")
        
    printer_error = False
    
    for p in printers:
        status = str(p.get("PrinterStatus", ""))
        evidence.append(f"Printer: {p.get('Name')} | Status: {status}")
        if status.lower() not in ["3", "normal", "0"]: # Simplified checking
            # WMI PrinterStatus 3 is Idle/Normal
            pass
            
    if len(printers) == 0:
        evidence.append("No printer is currently installed.")
        
    status = "healthy"
    if spooler.lower() != "running":
        status = "problem"
        
    return {
        "category": "printer",
        "status": status,
        "spooler_running": (spooler.lower() == "running"),
        "printers_installed": len(printers),
        "evidence": evidence
    }
''',

    "battery.py": '''
def check_battery():
    evidence = []
    
    batteries = parse_json(run_ps("Get-CimInstance -ClassName Win32_Battery -ErrorAction SilentlyContinue | Select-Object Name, EstimatedChargeRemaining, BatteryStatus | ConvertTo-Json -Compress"))
    
    if not batteries:
        evidence.append("No battery detected.")
        return {
            "category": "battery",
            "status": "healthy", # Desktops don't have batteries, healthy fallback
            "battery_present": False,
            "evidence": evidence
        }
        
    bat = batteries[0]
    charge = bat.get("EstimatedChargeRemaining", 0)
    status_code = bat.get("BatteryStatus", 2)
    
    evidence.append(f"Battery: {bat.get('Name')}")
    evidence.append(f"Charge remaining: {charge}%")
    
    # Status 1=Discharging, 2=AC, 3=Fully Charged, 4=Low, 5=Critical, 6=Charging
    is_charging = status_code in [2, 6, 3]
    evidence.append("State: AC/Charging" if is_charging else "State: Discharging")
    
    status = "healthy"
    if charge < 10 and not is_charging:
        status = "problem"
        evidence.append("Battery is critically low and not charging.")
        
    return {
        "category": "battery",
        "status": status,
        "battery_present": True,
        "charge_percent": charge,
        "is_charging": is_charging,
        "evidence": evidence
    }
''',

    "storage.py": '''
def check_storage():
    evidence = []
    
    disks = parse_json(run_ps("Get-Volume | Where-Object DriveType -eq 'Fixed' | Select-Object DriveLetter, SizeRemaining, Size | ConvertTo-Json -Compress"))
    
    storage_error = False
    
    for d in disks:
        letter = d.get("DriveLetter")
        if not letter: continue
        free_gb = int(d.get("SizeRemaining", 0)) / (1024**3)
        total_gb = int(d.get("Size", 1)) / (1024**3)
        pct_free = (free_gb / total_gb) * 100 if total_gb > 0 else 0
        
        evidence.append(f"Drive {letter}: {free_gb:.1f} GB free of {total_gb:.1f} GB ({pct_free:.1f}% free)")
        
        if pct_free < 5:
            storage_error = True
            evidence.append(f"CRITICAL: Drive {letter}: is critically low on space.")
            
    status = "problem" if storage_error else "healthy"
    
    return {
        "category": "storage",
        "status": status,
        "storage_error": storage_error,
        "evidence": evidence
    }
''',

    "performance.py": '''
def check_performance():
    evidence = []
    
    # Get basic CPU/RAM snapshots
    cpu = run_ps("(Get-WmiObject win32_processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average)")
    mem = parse_json(run_ps("Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory, TotalVisibleMemorySize | ConvertTo-Json -Compress"))
    
    try:
        cpu_load = int(cpu) if cpu else 0
    except:
        cpu_load = 0
        
    mem_load = 0
    if mem and len(mem) > 0:
        free = int(mem[0].get("FreePhysicalMemory", 0))
        total = int(mem[0].get("TotalVisibleMemorySize", 1))
        mem_load = ((total - free) / total) * 100
        
    evidence.append(f"CPU Utilization: {cpu_load}%")
    evidence.append(f"Memory Utilization: {mem_load:.1f}%")
    
    status = "healthy"
    if cpu_load > 95:
        evidence.append("CPU is experiencing extremely high sustained load.")
        status = "problem"
    if mem_load > 95:
        evidence.append("Memory is almost entirely exhausted.")
        status = "problem"
        
    return {
        "category": "performance",
        "status": status,
        "cpu_load": cpu_load,
        "mem_load": mem_load,
        "evidence": evidence
    }
''',

    "drivers.py": '''
def check_drivers():
    evidence = []
    
    errors = parse_json(run_ps("Get-PnpDevice -Status Error -ErrorAction SilentlyContinue | Select-Object Class, Name, Status | ConvertTo-Json -Compress"))
    
    driver_error = len(errors) > 0
    
    if driver_error:
        evidence.append(f"Detected {len(errors)} devices with driver errors.")
        for e in errors:
            evidence.append(f"[{e.get('Class')}] {e.get('Name')}")
    else:
        evidence.append("No devices reporting driver errors.")
        
    status = "problem" if driver_error else "healthy"
    
    return {
        "category": "drivers",
        "status": status,
        "error_count": len(errors),
        "evidence": evidence
    }
''',

    "windows.py": '''
def check_windows():
    evidence = []
    
    wuauserv = run_ps("(Get-Service -Name wuauserv -ErrorAction SilentlyContinue).Status")
    
    if wuauserv.lower() != "running":
        evidence.append("Windows Update Service is not running.")
    else:
        evidence.append("Windows Update Service is running.")
        
    # Get last critical event from system log in past 24h
    events = parse_json(run_ps("Get-EventLog -LogName System -EntryType Error -Newest 1 -ErrorAction SilentlyContinue | Select-Object Source, Message | ConvertTo-Json -Compress"))
    
    if events and len(events) > 0:
        evidence.append(f"Recent System Error: {events[0].get('Source')}")
        
    # For Windows general category, unless service is stopped/disabled manually, we can consider healthy
    status = "healthy"
    if wuauserv.lower() == "stopped":
        status = "problem"
        
    return {
        "category": "windows",
        "status": status,
        "wuauserv_running": (wuauserv.lower() == "running"),
        "evidence": evidence
    }
'''
}

for filename, content in modules.items():
    filepath = os.path.join(base_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(shared_header + content)
