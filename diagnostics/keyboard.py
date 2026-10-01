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

def check_keyboard():
    evidence = []
    
    keyboards = parse_json(run_ps("Get-PnpDevice -Class Keyboard -ErrorAction SilentlyContinue | Select-Object Name, Status, Present, Problem, ProblemDescription | ConvertTo-Json -Compress"))
    
    kb_error = False
    kb_present = len(keyboards) > 0
    
    for k in keyboards:
        status = str(k.get("Status", "")).upper()
        prob = k.get("Problem")
        prob_desc = k.get("ProblemDescription")
        if status == "ERROR": kb_error = True
        if prob is not None and prob != 0 and prob_desc:
            evidence.append(f"Keyboard: {k.get('Name')} | Status: {status} | PnP Code: {prob} ({prob_desc})")
        else:
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
