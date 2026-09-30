import subprocess
import time
import json
import os
import ctypes
from datetime import datetime

class RepairState:
    NOT_STARTED = "NOT_STARTED"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    RUNNING = "RUNNING"
    EXECUTED = "EXECUTED"
    VERIFICATION_RUNNING = "VERIFICATION_RUNNING"
    VERIFIED_FIXED = "VERIFIED_FIXED"
    EXECUTED_NOT_FIXED = "EXECUTED_NOT_FIXED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REQUIRES_ADMIN = "REQUIRES_ADMIN"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_cmd(cmd, timeout=30):
    start_time = time.time()
    result = {
        "command": cmd,
        "start_time": datetime.now().isoformat(),
        "stdout": "",
        "stderr": "",
        "exit_code": -1,
        "timeout": False,
        "exception": None
    }
    
    try:
        process = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        result["stdout"] = process.stdout
        result["stderr"] = process.stderr
        result["exit_code"] = process.returncode
    except subprocess.TimeoutExpired as e:
        result["timeout"] = True
        if hasattr(e, 'stdout') and e.stdout:
            result["stdout"] = e.stdout.decode('utf-8', errors='ignore') if isinstance(e.stdout, bytes) else str(e.stdout)
        if hasattr(e, 'stderr') and e.stderr:
            result["stderr"] = e.stderr.decode('utf-8', errors='ignore') if isinstance(e.stderr, bytes) else str(e.stderr)
    except Exception as e:
        result["exception"] = str(e)
        
    result["end_time"] = datetime.now().isoformat()
    result["duration"] = time.time() - start_time
    
    return result

def run_verify_cmd(cmd, match=None, is_bool=False):
    res = run_cmd(cmd)
    if res["exit_code"] != 0 or res["stderr"].strip():
        raise Exception(f"Verification command failed. Exit code: {res['exit_code']}, Stderr: {res['stderr']}")
    stdout = res["stdout"].strip()
    if is_bool:
        if stdout.lower() == "true": return True
        if stdout.lower() == "false": return False
        raise Exception(f"Unexpected boolean output: {stdout}")
    if match:
        return match.lower() in stdout.lower()
    return True

class RepairEngine:
    def __init__(self):
        self.log_file = "repair_log.jsonl"
        self.repairs = {
            "enable_wifi": {
                "name": "Enable Wi-Fi Adapter",
                "risk": "low",
                "description": "Enables the disabled Wi-Fi adapter.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Enable-NetAdapter -Name 'Wi-Fi' -Confirm:$false"),
                "verify": lambda: run_verify_cmd("(Get-NetAdapter -Name 'Wi-Fi' -ErrorAction Stop).Status", match="Up")
            },
            "restart_wlan": {
                "name": "Restart WLAN Service",
                "risk": "low",
                "description": "Restarts the Windows wireless service.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name WlanSvc -Force"),
                "verify": lambda: run_verify_cmd("(Get-Service -Name WlanSvc -ErrorAction Stop).Status", match="Running")
            },
            "ip_renew": {
                "name": "Renew IP Address",
                "risk": "low",
                "description": "Releases and renews your IP address from the DHCP server.",
                "requires_admin": False,
                "execute": lambda: run_cmd("ipconfig /release; ipconfig /renew"),
                "verify": lambda: run_verify_cmd("Test-Connection -ComputerName 8.8.8.8 -Count 1 -Quiet -ErrorAction Stop", is_bool=True)
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
                "verify": lambda: run_verify_cmd("(Get-Service -Name AudioSrv -ErrorAction Stop).Status", match="Running")
            },
            "restart_bluetooth": {
                "name": "Restart Bluetooth Service",
                "risk": "low",
                "description": "Restarts the Windows Bluetooth Support service.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name bthserv -Force"),
                "verify": lambda: run_verify_cmd("(Get-Service -Name bthserv -ErrorAction Stop).Status", match="Running")
            },
            "enable_camera": {
                "name": "Enable Camera Device",
                "risk": "low",
                "description": "Attempts to enable the camera device using PnP.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Get-PnpDevice -Class Camera, Image -Status Error | Enable-PnpDevice -Confirm:$false"),
                "verify": lambda: run_verify_cmd("(Get-PnpDevice -Class Camera, Image -ErrorAction Stop).Status", match="OK")
            },
            "restart_spooler": {
                "name": "Restart Print Spooler",
                "risk": "low",
                "description": "Restarts the Windows Print Spooler service.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name Spooler -Force"),
                "verify": lambda: run_verify_cmd("(Get-Service -Name Spooler -ErrorAction Stop).Status", match="Running")
            },
            "restart_wuauserv": {
                "name": "Restart Windows Update Service",
                "risk": "low",
                "description": "Restarts the Windows Update service to fix stuck updates.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name wuauserv -Force"),
                "verify": lambda: run_verify_cmd("(Get-Service -Name wuauserv -ErrorAction Stop).Status", match="Running")
            }
        }
        
    def get_available_repairs(self):
        return self.repairs
        
    def log_repair(self, log_entry):
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except:
            pass
            
    def execute_repair(self, repair_id, diagnostic_id="unknown", reason="user_confirmed"):
        repair = self.repairs.get(repair_id)
        if not repair:
            return {
                "state": RepairState.FAILED,
                "msg": f"Repair ID '{repair_id}' not found in strict catalog."
            }
            
        requires_admin = repair.get("requires_admin", False)
        if requires_admin and not is_admin():
            return {
                "state": RepairState.REQUIRES_ADMIN,
                "msg": "This repair requires Administrator permission."
            }
            
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "diagnostic_id": diagnostic_id,
            "repair_id": repair_id,
            "reason": reason,
            "confirmation": True,
            "elevation_required": requires_admin,
            "execution_started": datetime.now().isoformat(),
        }

        exec_result = repair["execute"]()
        log_entry["execution_finished"] = exec_result.get("end_time")
        log_entry["exit_code"] = exec_result.get("exit_code")
        log_entry["stdout"] = exec_result.get("stdout")
        log_entry["stderr"] = exec_result.get("stderr")
        
        if exec_result.get("timeout"):
            log_entry["error"] = "Command timed out."
            self.log_repair(log_entry)
            return {
                "state": RepairState.FAILED,
                "msg": "Repair execution failed due to timeout.",
                "details": exec_result
            }
            
        if exec_result.get("exception"):
            log_entry["error"] = exec_result.get("exception")
            self.log_repair(log_entry)
            return {
                "state": RepairState.FAILED,
                "msg": f"Repair execution failed: {exec_result.get('exception')}",
                "details": exec_result
            }
            
        if exec_result.get("exit_code") != 0:
            log_entry["error"] = f"Non-zero exit code: {exec_result.get('exit_code')}"
            self.log_repair(log_entry)
            return {
                "state": RepairState.FAILED,
                "msg": f"Repair execution failed. Exit code: {exec_result.get('exit_code')}. Stderr: {exec_result.get('stderr')}",
                "details": exec_result
            }
            
        self.log_repair(log_entry)
        return {
            "state": RepairState.EXECUTED,
            "msg": "Repair executed successfully.",
            "details": exec_result
        }

    def verify_repair(self, repair_id):
        repair = self.repairs.get(repair_id)
        if not repair:
            return RepairState.VERIFICATION_FAILED
        verify_func = repair.get("verify")
        if not verify_func:
            return RepairState.VERIFICATION_FAILED
        try:
            res = verify_func()
            if res is True:
                return RepairState.VERIFIED_FIXED
            elif res is False:
                return RepairState.EXECUTED_NOT_FIXED
            return RepairState.VERIFICATION_FAILED
        except Exception as e:
            # Log verification failure optionally
            print(f"Verification error for {repair_id}: {e}")
            return RepairState.VERIFICATION_FAILED
