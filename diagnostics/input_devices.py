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

def check_input():
    evidence = []
    
    mice = parse_json(run_ps("Get-PnpDevice -Class Mouse -ErrorAction SilentlyContinue | Select-Object Name, Status, Present, Problem, ProblemDescription | ConvertTo-Json -Compress"))
    
    mouse_error = False
    mouse_present = len(mice) > 0
    
    for m in mice:
        status = str(m.get("Status", "")).upper()
        prob = m.get("Problem")
        prob_desc = m.get("ProblemDescription")
        if status == "ERROR": mouse_error = True
        if prob is not None and prob != 0 and prob_desc:
            evidence.append(f"Mouse/Touchpad: {m.get('Name')} | Status: {status} | PnP Code: {prob} ({prob_desc})")
        else:
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
