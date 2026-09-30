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

def check_storage():
    evidence = []
    
    disks = parse_json(run_ps("Get-Volume | Where-Object DriveType -eq 'Fixed' | Select-Object DriveLetter, SizeRemaining, Size | ConvertTo-Json -Compress"))
    
    storage_error = False
    
    for d in disks:
        letter = d.get("DriveLetter")
        if not letter: continue
        free_gb = int(d.get("SizeRemaining", 0)) / (1024**3)
        total_gb = int(d.get("Size", 1)) / (1024**3)
        pct_free = (free_gb / total_gb) * 100 if total_gb > 0 else 0
        
        evidence.append(f"Drive {letter}: {free_gb:.1f} GB free of {total_gb:.1f} GB ({pct_free:.1f}% free)")
        
        if pct_free < 5:
            storage_error = True
            evidence.append(f"CRITICAL: Drive {letter}: is critically low on space.")
            
    status = "problem" if storage_error else "healthy"
    
    return {
        "category": "storage",
        "status": status,
        "storage_error": storage_error,
        "evidence": evidence
    }
