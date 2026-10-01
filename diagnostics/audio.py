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

def check_audio():
    evidence = []
    
    # Check services
    audiosrv = run_ps("(Get-Service -Name AudioSrv -ErrorAction SilentlyContinue).Status")
    audioendpoint = run_ps("(Get-Service -Name AudioEndpointBuilder -ErrorAction SilentlyContinue).Status")
    
    # Check audio devices
    devices = parse_json(run_ps("Get-PnpDevice -Class Media -ErrorAction SilentlyContinue | Select-Object Name, Status, Present, Problem, ProblemDescription | ConvertTo-Json -Compress"))
    
    if audiosrv.lower() != "running":
        evidence.append("Windows Audio Service (AudioSrv) is stopped.")
    if audioendpoint.lower() != "running":
        evidence.append("Windows Audio Endpoint Builder Service is stopped.")
        
    device_error = False
    device_present = len(devices) > 0
    device_enabled = False
    
    for d in devices:
        status = str(d.get("Status", "")).upper()
        prob = d.get("Problem")
        prob_desc = d.get("ProblemDescription")
        if status == "ERROR": device_error = True
        elif status == "OK": device_enabled = True
        
        if prob is not None and prob != 0 and prob_desc:
            evidence.append(f"Device: {d.get('Name')} | Status: {status} | PnP Code: {prob} ({prob_desc})")
        else:
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
