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

def check_performance():
    evidence = []
    
    # Get basic CPU/RAM snapshots
    cpu = run_ps("(Get-WmiObject win32_processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average)")
    mem = parse_json(run_ps("Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory, TotalVisibleMemorySize | ConvertTo-Json -Compress"))
    
    try:
        cpu_load = int(cpu) if cpu else 0
    except:
        cpu_load = 0
        
    mem_load = 0
    if mem and len(mem) > 0:
        free = int(mem[0].get("FreePhysicalMemory", 0))
        total = int(mem[0].get("TotalVisibleMemorySize", 1))
        mem_load = ((total - free) / total) * 100
        
    evidence.append(f"CPU Utilization: {cpu_load}%")
    evidence.append(f"Memory Utilization: {mem_load:.1f}%")
    
    status = "healthy"
    if cpu_load > 95:
        evidence.append("CPU is experiencing extremely high sustained load.")
        status = "problem"
    if mem_load > 95:
        evidence.append("Memory is almost entirely exhausted.")
        status = "problem"
        
    return {
        "category": "performance",
        "status": status,
        "cpu_load": cpu_load,
        "mem_load": mem_load,
        "evidence": evidence
    }
