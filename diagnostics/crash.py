import subprocess
import json

def check_crashes():
    cmd = '''
    Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2; StartTime=(Get-Date).AddDays(-1)} -ErrorAction SilentlyContinue |
    Select-Object TimeCreated, Id, ProviderName, Message -First 5 |
    ConvertTo-Json -Compress
    '''
    try:
        result = subprocess.check_output(["powershell", "-Command", cmd], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if not result.strip():
            return {"category": "crash", "recent_crashes": []}
        data = json.loads(result)
        if isinstance(data, dict): data = [data]
        return {"category": "crash", "recent_crashes": data}
    except:
        return {"category": "crash", "recent_crashes": []}
