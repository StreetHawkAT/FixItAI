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
