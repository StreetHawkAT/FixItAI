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
