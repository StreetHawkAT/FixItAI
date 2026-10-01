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

def check_display():
    evidence = []
    
    gpus = parse_json(run_ps("Get-PnpDevice -Class Display -ErrorAction SilentlyContinue | Select-Object Name, Status, Present, Problem, ProblemDescription | ConvertTo-Json -Compress"))
    monitors = parse_json(run_ps("Get-PnpDevice -Class Monitor -ErrorAction SilentlyContinue | Select-Object Name, Status, Present, Problem, ProblemDescription | ConvertTo-Json -Compress"))
    
    gpu_error = False
    gpu_present = len(gpus) > 0
    
    for g in gpus:
        status = str(g.get("Status", "")).upper()
        prob = g.get("Problem")
        prob_desc = g.get("ProblemDescription")
        if status == "ERROR": gpu_error = True
        if prob is not None and prob != 0 and prob_desc:
            evidence.append(f"GPU: {g.get('Name')} | Status: {status} | PnP Code: {prob} ({prob_desc})")
        else:
            evidence.append(f"GPU: {g.get('Name')} | Status: {status}")
        
    for m in monitors:
        status = str(m.get("Status", "")).upper()
        prob = m.get("Problem")
        prob_desc = m.get("ProblemDescription")
        if prob is not None and prob != 0 and prob_desc:
            evidence.append(f"Monitor: {m.get('Name')} | Status: {status} | PnP Code: {prob} ({prob_desc})")
        else:
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
