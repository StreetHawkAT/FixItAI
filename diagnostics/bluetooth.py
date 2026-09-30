import subprocess
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
