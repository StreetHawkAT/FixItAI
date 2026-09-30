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

def check_battery():
    evidence = []
    
    batteries = parse_json(run_ps("Get-CimInstance -ClassName Win32_Battery -ErrorAction SilentlyContinue | Select-Object Name, EstimatedChargeRemaining, BatteryStatus | ConvertTo-Json -Compress"))
    
    if not batteries:
        evidence.append("No battery detected.")
        return {
            "category": "battery",
            "status": "healthy", # Desktops don't have batteries, healthy fallback
            "battery_present": False,
            "evidence": evidence
        }
        
    bat = batteries[0]
    charge = bat.get("EstimatedChargeRemaining", 0)
    status_code = bat.get("BatteryStatus", 2)
    
    evidence.append(f"Battery: {bat.get('Name')}")
    evidence.append(f"Charge remaining: {charge}%")
    
    # Status 1=Discharging, 2=AC, 3=Fully Charged, 4=Low, 5=Critical, 6=Charging
    is_charging = status_code in [2, 6, 3]
    evidence.append("State: AC/Charging" if is_charging else "State: Discharging")
    
    status = "healthy"
    if charge < 10 and not is_charging:
        status = "problem"
        evidence.append("Battery is critically low and not charging.")
        
    return {
        "category": "battery",
        "status": status,
        "battery_present": True,
        "charge_percent": charge,
        "is_charging": is_charging,
        "evidence": evidence
    }
