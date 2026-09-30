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

def check_camera():
    devices_json = run_ps("Get-PnpDevice -Class Camera, Image -ErrorAction SilentlyContinue | Select-Object Name, Status, Present, Class | ConvertTo-Json -Compress")
    devices = []
    
    if devices_json:
        try:
            parsed = json.loads(devices_json)
            if isinstance(parsed, dict):
                devices = [parsed]
            elif isinstance(parsed, list):
                devices = parsed
        except:
            pass

    camera_present = len(devices) > 0
    camera_enabled = False
    driver_error = False
    device_status = "not_detected"
    
    evidence = []
    
    if camera_present:
        evidence.append(f"Detected {len(devices)} camera/imaging device(s).")
        
        has_ok = False
        for d in devices:
            status = str(d.get("Status", "")).upper()
            if status == "OK":
                has_ok = True
                camera_enabled = True
            elif status == "ERROR":
                driver_error = True
            
            evidence.append(f"Device: {d.get('Name')} | Status: {status}")
            
        if has_ok:
            device_status = "ok"
        elif driver_error:
            device_status = "error"
        else:
            device_status = "disabled" # Usually if it's not OK and not Error, it might be Unknown or Degraded
            
        # Check if disabled by checking for 'Error' or we can check explicitly if device is disabled. 
        # In PnP, disabled devices often have status 'Error' or 'Unknown'.
        # Let's check explicitly for disabled
        # Actually, Get-PnpDevice reports 'Error' when disabled via Device Manager.
    else:
        evidence.append("No camera device was detected by Windows.")
        
    status = "healthy"
    if not camera_present:
        status = "problem"
    elif driver_error or not camera_enabled:
        status = "problem"

    return {
        "category": "camera",
        "status": status,
        "camera_present": camera_present,
        "camera_enabled": camera_enabled,
        "driver_status": "error" if driver_error else "ok",
        "device_status": device_status,
        "devices": devices,
        "evidence": evidence
    }
