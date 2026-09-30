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
