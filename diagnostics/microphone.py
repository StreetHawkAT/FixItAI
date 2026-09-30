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
