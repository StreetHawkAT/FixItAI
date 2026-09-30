import subprocess
import time

def run_cmd(cmd):
    try:
        subprocess.check_output(["powershell", "-Command", cmd], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True, "Success"
    except subprocess.CalledProcessError as e:
        return False, f"Failed: {e}"

class RepairEngine:
    def __init__(self):
        self.repairs = {
            "enable_wifi": {
                "name": "Enable Wi-Fi Adapter",
                "risk": "low",
                "description": "Enables the disabled Wi-Fi adapter.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Enable-NetAdapter -Name 'Wi-Fi' -Confirm:$false"),
                "verify": lambda: "Up" in run_cmd("(Get-NetAdapter -Name 'Wi-Fi' -ErrorAction SilentlyContinue).Status")[1]
            },
            "restart_wlan": {
                "name": "Restart WLAN Service",
                "risk": "low",
                "description": "Restarts the Windows wireless service.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name WlanSvc -Force"),
                "verify": lambda: "Running" in run_cmd("(Get-Service -Name WlanSvc -ErrorAction SilentlyContinue).Status")[1]
            },
            "ip_renew": {
                "name": "Renew IP Address",
                "risk": "low",
                "description": "Releases and renews your IP address from the DHCP server.",
                "requires_admin": False,
                "execute": lambda: run_cmd("ipconfig /release; ipconfig /renew"),
                "verify": lambda: "Success" in run_cmd("Test-Connection -ComputerName 8.8.8.8 -Count 1 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Status")[1]
            },
            "flush_dns": {
                "name": "Flush DNS Cache",
                "risk": "low",
                "description": "Clears the DNS resolver cache.",
                "requires_admin": False,
                "execute": lambda: run_cmd("ipconfig /flushdns"),
                "verify": lambda: True
            },
            "restart_audio": {
                "name": "Restart Audio Service",
                "risk": "low",
                "description": "Restarts the Windows Audio service.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name AudioSrv -Force"),
                "verify": lambda: "Running" in run_cmd("(Get-Service -Name AudioSrv).Status")[1]
            },
            "restart_bluetooth": {
                "name": "Restart Bluetooth Service",
                "risk": "low",
                "description": "Restarts the Windows Bluetooth Support service.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name bthserv -Force"),
                "verify": lambda: "Running" in run_cmd("(Get-Service -Name bthserv).Status")[1]
            },
            "enable_camera": {
                "name": "Enable Camera Device",
                "risk": "low",
                "description": "Attempts to enable the camera device using PnP.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Get-PnpDevice -Class Camera, Image -Status Error | Enable-PnpDevice -Confirm:$false"),
                "verify": lambda: "OK" in run_cmd("(Get-PnpDevice -Class Camera, Image).Status")[1]
            },
            "restart_spooler": {
                "name": "Restart Print Spooler",
                "risk": "low",
                "description": "Restarts the Windows Print Spooler service.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name Spooler -Force"),
                "verify": lambda: "Running" in run_cmd("(Get-Service -Name Spooler).Status")[1]
            },
            "restart_wuauserv": {
                "name": "Restart Windows Update Service",
                "risk": "low",
                "description": "Restarts the Windows Update service to fix stuck updates.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name wuauserv -Force"),
                "verify": lambda: "Running" in run_cmd("(Get-Service -Name wuauserv).Status")[1]
            }
        }
        
    def get_available_repairs(self):
        return self.repairs
        
    def execute_repair(self, repair_id):
        repair = self.repairs.get(repair_id)
        if not repair:
            return False, "Repair ID not found in strict catalog."
        return repair["execute"]()

    def verify_repair(self, repair_id):
        repair = self.repairs.get(repair_id)
        if not repair:
            return False
        try:
            return repair["verify"]()
        except:
            return False
