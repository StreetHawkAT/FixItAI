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

def check_printer():
    evidence = []
    
    spooler = run_ps("(Get-Service -Name Spooler -ErrorAction SilentlyContinue).Status")
    printers = parse_json(run_ps("Get-Printer | Select-Object Name, PrinterStatus | ConvertTo-Json -Compress"))
    
    if spooler.lower() != "running":
        evidence.append("Print Spooler Service is stopped.")
        
    printer_error = False
    
    for p in printers:
        status = str(p.get("PrinterStatus", ""))
        evidence.append(f"Printer: {p.get('Name')} | Status: {status}")
        if status.lower() not in ["3", "normal", "0"]: # Simplified checking
            # WMI PrinterStatus 3 is Idle/Normal
            pass
            
    if len(printers) == 0:
        evidence.append("No printer is currently installed.")
        
    status = "healthy"
    if spooler.lower() != "running":
        status = "problem"
        
    return {
        "category": "printer",
        "status": status,
        "spooler_running": (spooler.lower() == "running"),
        "printers_installed": len(printers),
        "evidence": evidence
    }
