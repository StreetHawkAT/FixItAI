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

def verify_camera_pnp(engine=None):
    """
    Re-queries Windows PnP state for Camera and Image class devices.
    Returns:
        True  -> all detected camera devices report Status == 'OK' and Problem in (0, None).
        False -> at least one camera device remains in Error/Disabled state, or 0 devices found.
    Raises:
        Exception -> if the command fails, times out, or output is unparseable.
    """
    cmd = "@(Get-PnpDevice -Class Camera, Image -ErrorAction SilentlyContinue | Select-Object Name, Status, Present, Class, InstanceId, Problem, ProblemDescription) | ConvertTo-Json -Compress"
    res = run_cmd(cmd)
    if res.get("timeout") is True:
        raise Exception("Verification command timed out while querying camera PnP devices.")
    if res.get("exception"):
        raise Exception(f"Verification command encountered an exception: {res.get('exception')}")
    if res.get("exit_code") != 0:
        raise Exception(f"Verification command failed with exit code {res.get('exit_code')}: {res.get('stderr')}")

    stdout = res.get("stdout", "").strip()
    if not stdout or stdout == "null":
        if engine:
            engine.last_verification_details = {
                "repair_id": "enable_camera",
                "healthy_devices": [],
                "problem_devices": [],
                "evidence": ["No camera devices detected after repair execution."]
            }
        return False

    try:
        data = json.loads(stdout)
    except Exception as e:
        raise Exception(f"Failed to parse PnP device JSON output: {e}. Raw: {stdout}")

    devices = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
    if not devices:
        if engine:
            engine.last_verification_details = {
                "repair_id": "enable_camera",
                "healthy_devices": [],
                "problem_devices": [],
                "evidence": ["No camera devices detected after repair execution."]
            }
        return False

    healthy_devices = []
    problem_devices = []

    for d in devices:
        name = d.get("Name") or d.get("FriendlyName") or "Camera device"
        status = str(d.get("Status", "")).upper()
        prob = d.get("Problem")
        desc = d.get("ProblemDescription") or ""

        if status == "OK" and (prob == 0 or prob is None):
            healthy_devices.append(name)
        else:
            problem_devices.append({
                "name": name,
                "status": status,
                "problem": prob,
                "description": desc
            })

    evidence = [f"Detected {len(devices)} camera device(s)."]
    for h in healthy_devices:
        evidence.append(f"Device: {h} | Status: OK | PnP Code: 0 (Working properly)")
    for p in problem_devices:
        evidence.append(f"Device: {p['name']} | Status: {p['status']} | PnP Code: {p['problem']} ({p['description']})")

    if engine:
        engine.last_verification_details = {
            "repair_id": "enable_camera",
            "healthy_devices": healthy_devices,
            "problem_devices": problem_devices,
            "evidence": evidence
        }

    # If any camera device is in an error or disabled state, repair is not verified fixed
    if problem_devices:
        return False

    # Only return True if at least one device was found and verified healthy
    return len(healthy_devices) > 0

def is_service_running(status_val):
    if status_val == 4 or str(status_val).strip().lower() in ("running", "4"):
        return True
    return False

def verify_service_status(service_name, display_name=None, engine=None, repair_id=None):
    disp = display_name or service_name
    cmd = f"@(Get-Service -Name '{service_name}' -ErrorAction SilentlyContinue) | Select-Object Name, Status | ConvertTo-Json -Compress"
    res = run_cmd(cmd)
    if res.get("timeout") is True:
        raise Exception(f"Verification command timed out while querying service '{service_name}'.")
    if res.get("exception"):
        raise Exception(f"Verification exception: {res.get('exception')}")
    if res.get("exit_code") != 0:
        raise Exception(f"Verification command failed with exit code {res.get('exit_code')}: {res.get('stderr')}")
    
    stdout = res.get("stdout", "").strip()
    if not stdout or stdout == "null":
        raise Exception(f"Service '{service_name}' not found on this system.")
        
    try:
        data = json.loads(stdout)
        if isinstance(data, dict):
            raw_status = data.get("Status", stdout)
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            raw_status = data[0].get("Status", stdout)
        else:
            raw_status = data
    except Exception:
        raw_status = stdout
        
    running = is_service_running(raw_status)
    status_str = "Running" if running else ("Stopped" if raw_status in (1, "1") else str(raw_status))
    
    if engine and repair_id:
        engine.last_verification_details = {
            "repair_id": repair_id,
            "service": service_name,
            "status": status_str,
            "evidence": [f"{disp} ({service_name}) status: {status_str}"]
        }
        
    return running

def verify_wifi_adapter(engine=None):
    cmd = "@(Get-NetAdapter -ErrorAction SilentlyContinue) | Select-Object Name, InterfaceDescription, Status, AdminStatus | ConvertTo-Json -Compress"
    res = run_cmd(cmd)
    if res.get("timeout") is True:
        raise Exception("Verification command timed out while querying network adapters.")
    if res.get("exception"):
        raise Exception(f"Verification exception: {res.get('exception')}")
    if res.get("exit_code") != 0:
        raise Exception(f"Verification command failed with exit code {res.get('exit_code')}: {res.get('stderr')}")
        
    stdout = res.get("stdout", "").strip()
    if not stdout or stdout == "null":
        if engine:
            engine.last_verification_details = {
                "repair_id": "enable_wifi",
                "evidence": ["No network adapters found on this system."]
            }
        return False
        
    try:
        data = json.loads(stdout)
    except Exception as e:
        if stdout.strip().lower() in ("up", "1"):
            if engine:
                engine.last_verification_details = {"repair_id": "enable_wifi", "evidence": ["Wi-Fi adapter is Up."]}
            return True
        elif stdout.strip().lower() in ("disabled", "down", "disconnected"):
            if engine:
                engine.last_verification_details = {"repair_id": "enable_wifi", "evidence": [f"Wi-Fi adapter is {stdout}."]}
            return False
        raise Exception(f"Failed to parse network adapter JSON output: {e}. Raw: {stdout}")
        
    adapters = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
    
    wifi_adapters = []
    for a in adapters:
        name = str(a.get("Name", "")).lower()
        desc = str(a.get("InterfaceDescription", "")).lower()
        if "wi-fi" in name or "wifi" in name or "wireless" in name or "802.11" in desc or "wi-fi" in desc or "wifi" in desc:
            wifi_adapters.append(a)
            
    if not wifi_adapters:
        wifi_adapters = [a for a in adapters if str(a.get("Name", "")).strip() == "Wi-Fi"]
        
    if not wifi_adapters:
        if engine:
            engine.last_verification_details = {
                "repair_id": "enable_wifi",
                "evidence": ["No Wi-Fi / Wireless adapter detected on this system."]
            }
        return False
        
    evidence = []
    any_disabled = False
    enabled_count = 0
    for a in wifi_adapters:
        name = a.get("Name", "Wi-Fi")
        status = str(a.get("Status", "Unknown"))
        admin_st = a.get("AdminStatus")
        is_enabled = (admin_st in (1, "1", "Up", "up")) and (status.lower() != "disabled")
        if is_enabled:
            enabled_count += 1
            evidence.append(f"Wi-Fi adapter '{name}' is enabled (Status: {status}, AdminStatus: Up).")
        else:
            any_disabled = True
            evidence.append(f"Wi-Fi adapter '{name}' is disabled (Status: {status}, AdminStatus: {admin_st}).")
            
    if engine:
        engine.last_verification_details = {
            "repair_id": "enable_wifi",
            "evidence": evidence
        }
        
    return enabled_count > 0 and not any_disabled

def is_matching_adapter(alias, target):
    if not alias or not target:
        return False
    alias_lower = str(alias).strip().lower()
    target_lower = str(target).strip().lower()
    if alias_lower == target_lower:
        return True
    if target_lower in alias_lower:
        return True
    if "wi-fi" in target_lower or "wifi" in target_lower:
        return any(k in alias_lower for k in ("wi-fi", "wifi", "wireless", "wlan"))
    if "ethernet" in target_lower:
        return "ethernet" in alias_lower
    return False

def verify_ip_renew(engine=None, target_adapter=None):
    cmd = "@(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue) | Select-Object InterfaceAlias, IPAddress, PrefixOrigin | ConvertTo-Json -Compress"
    res = run_cmd(cmd)
    if res.get("timeout") is True:
        raise Exception("Verification command timed out while querying IP configuration.")
    if res.get("exception"):
        raise Exception(f"Verification exception: {res.get('exception')}")
    if res.get("exit_code") != 0:
        raise Exception(f"Verification command failed with exit code {res.get('exit_code')}: {res.get('stderr')}")
        
    stdout = res.get("stdout", "").strip()
    if not stdout or stdout == "null":
        if engine:
            engine.last_verification_details = {
                "repair_id": "ip_renew",
                "evidence": ["No IPv4 addresses found on this system."]
            }
        return False
        
    try:
        data = json.loads(stdout)
    except Exception as e:
        if stdout.lower() == "true":
            if engine:
                engine.last_verification_details = {"repair_id": "ip_renew", "evidence": ["Network connectivity verified."]}
            return True
        elif stdout.lower() == "false":
            if engine:
                engine.last_verification_details = {"repair_id": "ip_renew", "evidence": ["No valid IP / network connectivity."]}
            return False
        raise Exception(f"Failed to parse IP address JSON output: {e}. Raw: {stdout}")
        
    ip_list = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])

    # Determine target adapter (default to Wi-Fi for FixIt AI network repairs, or inspect engine)
    target = target_adapter
    if not target and engine and hasattr(engine, "target_adapter") and engine.target_adapter:
        target = engine.target_adapter
    if not target and engine and hasattr(engine, "last_diagnosis") and isinstance(engine.last_diagnosis, dict):
        if engine.last_diagnosis.get("target_adapter"):
            target = engine.last_diagnosis["target_adapter"]
        elif not engine.last_diagnosis.get("wifi_present") and engine.last_diagnosis.get("ethernet_present"):
            target = "Ethernet"
    if not target:
        target = "Wi-Fi"

    evidence = []
    target_entries = []
    unrelated_entries = []

    for entry in ip_list:
        alias = entry.get("InterfaceAlias", "Unknown")
        ip = entry.get("IPAddress", "")
        if not ip or ip.startswith("127.") or "loopback" in alias.lower():
            continue
        if is_matching_adapter(alias, target):
            target_entries.append((alias, ip))
        else:
            unrelated_entries.append((alias, ip))

    if not target_entries:
        evidence.append(f"Target network adapter '{target}' was not found or has no active IPv4 interface.")
        for alias, ip in unrelated_entries:
            evidence.append(f"Unrelated interface '{alias}' has IP {ip} (ignored).")
        if engine:
            engine.last_verification_details = {
                "repair_id": "ip_renew",
                "target_adapter": target,
                "evidence": evidence
            }
        return False

    valid_target_ips = []
    apipa_target_ips = []
    for alias, ip in target_entries:
        if ip.startswith("169.254.") or ip == "0.0.0.0":
            apipa_target_ips.append((alias, ip))
        else:
            valid_target_ips.append((alias, ip))

    for alias, ip in valid_target_ips:
        evidence.append(f"Target adapter '{alias}' has valid IPv4 address: {ip}")
    for alias, ip in apipa_target_ips:
        evidence.append(f"Target adapter '{alias}' has APIPA address: {ip} (DHCP lease failed)")
    for alias, ip in unrelated_entries:
        evidence.append(f"Unrelated interface '{alias}' has IP {ip} (ignored for {target} repair)")

    if engine:
        engine.last_verification_details = {
            "repair_id": "ip_renew",
            "target_adapter": target,
            "evidence": evidence
        }

    return len(valid_target_ips) > 0

def verify_dns_flush(engine=None):
    cmd_svc = "@(Get-Service -Name Dnscache -ErrorAction SilentlyContinue) | Select-Object Name, Status | ConvertTo-Json -Compress"
    res_svc = run_cmd(cmd_svc)
    if res_svc.get("timeout") is True:
        raise Exception("Verification timed out while querying DNS client service.")
    if res_svc.get("exception"):
        raise Exception(f"Verification exception: {res_svc.get('exception')}")
    if res_svc.get("exit_code") != 0:
        raise Exception(f"Verification command failed with exit code {res_svc.get('exit_code')}: {res_svc.get('stderr')}")
        
    stdout_svc = res_svc.get("stdout", "").strip()
    if not stdout_svc or stdout_svc == "null":
        raise Exception("DNS Client service (Dnscache) not found.")
        
    try:
        data_svc = json.loads(stdout_svc)
        if isinstance(data_svc, dict):
            raw_status = data_svc.get("Status", stdout_svc)
        elif isinstance(data_svc, list) and len(data_svc) > 0 and isinstance(data_svc[0], dict):
            raw_status = data_svc[0].get("Status", stdout_svc)
        else:
            raw_status = data_svc
    except Exception:
        raw_status = stdout_svc
        
    dnscache_running = is_service_running(raw_status)
    evidence = []
    if dnscache_running:
        evidence.append("DNS Client service (Dnscache) is Running.")
    else:
        evidence.append("DNS Client service (Dnscache) is Stopped.")
        if engine:
            engine.last_verification_details = {
                "repair_id": "flush_dns",
                "evidence": evidence
            }
        return False
        
    cmd_resolve = "Resolve-DnsName -Name 'localhost' -ErrorAction SilentlyContinue | Select-Object -First 1 Name, IPAddress | ConvertTo-Json -Compress"
    res_res = run_cmd(cmd_resolve)
    if res_res.get("exit_code") == 0 and res_res.get("stdout", "").strip():
        evidence.append("DNS resolver successfully resolved 'localhost'.")
        dns_resolved = True
    else:
        evidence.append("DNS resolver failed to resolve 'localhost'.")
        dns_resolved = False
        
    if engine:
        engine.last_verification_details = {
            "repair_id": "flush_dns",
            "evidence": evidence
        }
        
    return dnscache_running and dns_resolved

def verify_audio_services(engine=None):
    cmd = "@(Get-Service -Name AudioSrv, AudioEndpointBuilder -ErrorAction SilentlyContinue) | Select-Object Name, Status | ConvertTo-Json -Compress"
    res = run_cmd(cmd)
    if res.get("timeout") is True:
        raise Exception("Verification timed out while querying audio services.")
    if res.get("exception"):
        raise Exception(f"Verification exception: {res.get('exception')}")
    if res.get("exit_code") != 0:
        raise Exception(f"Verification command failed with exit code {res.get('exit_code')}: {res.get('stderr')}")
        
    stdout = res.get("stdout", "").strip()
    if not stdout or stdout == "null":
        raise Exception("Audio services not found on this system.")
        
    try:
        data = json.loads(stdout)
    except Exception:
        running = is_service_running(stdout)
        if engine:
            engine.last_verification_details = {
                "repair_id": "restart_audio",
                "evidence": [f"Audio service status: {'Running' if running else stdout}"]
            }
        return running
        
    services = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
    if not services:
        raise Exception("Audio services not found on this system.")
        
    all_running = True
    evidence = []
    for s in services:
        name = s.get("Name", "Unknown")
        st_val = s.get("Status")
        running = is_service_running(st_val)
        st_str = "Running" if running else "Stopped"
        evidence.append(f"Service {name}: {st_str}")
        if not running:
            all_running = False
            
    if engine:
        engine.last_verification_details = {
            "repair_id": "restart_audio",
            "evidence": evidence
        }
    return all_running

def verify_wuauserv_service(engine=None):
    cmd = "$s = Get-Service -Name wuauserv -ErrorAction SilentlyContinue; $c = Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object Name -eq 'wuauserv'; [PSCustomObject]@{ Name = $s.Name; Status = $s.Status; StartType = $s.StartType; ExitCode = if ($c) { $c.ExitCode } else { 0 }; StartMode = if ($c) { $c.StartMode } else { 'Unknown' } } | ConvertTo-Json -Compress"
    res = run_cmd(cmd)
    if res.get("timeout") is True:
        raise Exception("Verification command timed out while querying Windows Update service.")
    if res.get("exception"):
        raise Exception(f"Verification exception: {res.get('exception')}")
    if res.get("exit_code") != 0:
        raise Exception(f"Verification command failed with exit code {res.get('exit_code')}: {res.get('stderr')}")
        
    stdout = res.get("stdout", "").strip()
    if not stdout or stdout == "null":
        raise Exception("Windows Update service (wuauserv) not found on this system.")
        
    try:
        data = json.loads(stdout)
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
    except Exception as e:
        if stdout.lower() in ("running", "4"):
            data = {"Name": "wuauserv", "Status": 4}
        elif stdout.lower() in ("stopped", "1"):
            data = {"Name": "wuauserv", "Status": 1}
        else:
            raise Exception(f"Failed to parse wuauserv status JSON output: {e}. Raw: {stdout}")

    if not isinstance(data, dict):
        raise Exception(f"Unexpected data format querying wuauserv: {data}")

    raw_status = data.get("Status")
    start_type = data.get("StartType")
    exit_code = data.get("ExitCode")
    start_mode = data.get("StartMode")
    
    running = is_service_running(raw_status)
    evidence = []

    # 1. Service is actively running
    if running:
        evidence.append("Windows Update service (wuauserv) is actively Running.")
        if engine:
            engine.last_verification_details = {
                "repair_id": "restart_wuauserv",
                "service": "wuauserv",
                "status": "Running",
                "evidence": evidence
            }
        return True

    # 2. Service is disabled
    is_disabled = (start_type in (4, "4", "Disabled", "disabled")) or (str(start_mode).strip().lower() == "disabled")
    if is_disabled:
        evidence.append("Windows Update service (wuauserv) is Disabled. Service restart cannot function.")
        if engine:
            engine.last_verification_details = {
                "repair_id": "restart_wuauserv",
                "service": "wuauserv",
                "status": "Disabled",
                "evidence": evidence
            }
        return False

    # 3. Service stopped with non-zero exit code (crashed or failed to start)
    if exit_code is not None and exit_code != 0:
        evidence.append(f"Windows Update service (wuauserv) terminated abnormally with ExitCode {exit_code}.")
        if engine:
            engine.last_verification_details = {
                "repair_id": "restart_wuauserv",
                "service": "wuauserv",
                "status": f"Stopped (ExitCode {exit_code})",
                "evidence": evidence
            }
        return False

    # 4. Service stopped with ExitCode == 0 and enabled start type (clean trigger standby)
    is_trigger_standby = (start_type in (2, 3, "2", "3", "Manual", "Automatic", "manual", "automatic") or str(start_mode).strip().lower() in ("manual", "auto")) and (exit_code == 0)
    if is_trigger_standby:
        evidence.append(f"Windows Update service (wuauserv) is in healthy trigger standby (ExitCode: 0, StartType: {start_type or start_mode}). Ready to service on-demand.")
        if engine:
            engine.last_verification_details = {
                "repair_id": "restart_wuauserv",
                "service": "wuauserv",
                "status": "Trigger Standby (Healthy)",
                "evidence": evidence
            }
        return True

    # 5. Service stopped without clean trigger standby evidence (e.g. legacy/ambiguous stopped status)
    evidence.append("Windows Update service (wuauserv) is Stopped.")
    if engine:
        engine.last_verification_details = {
            "repair_id": "restart_wuauserv",
            "service": "wuauserv",
            "status": "Stopped",
            "evidence": evidence
        }
    return False

class RepairEngine:
    def __init__(self):
        self.log_file = "repair_log.jsonl"
        self.last_verification_details = None
        self.last_verification_error = None
        self.repairs = {
            "enable_wifi": {
                "name": "Enable Wi-Fi Adapter",
                "risk": "low",
                "description": "Enables the disabled Wi-Fi adapter.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Enable-NetAdapter -Name 'Wi-Fi' -Confirm:$false"),
                "verify": lambda: verify_wifi_adapter(self)
            },
            "restart_wlan": {
                "name": "Restart WLAN Service",
                "risk": "low",
                "description": "Restarts the Windows wireless service.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name WlanSvc -Force"),
                "verify": lambda: verify_service_status("WlanSvc", "WLAN AutoConfig Service", engine=self, repair_id="restart_wlan")
            },
            "ip_renew": {
                "name": "Renew IP Address",
                "risk": "low",
                "description": "Releases and renews your IP address from the DHCP server.",
                "requires_admin": False,
                "execute": lambda: run_cmd("ipconfig /release; ipconfig /renew"),
                "verify": lambda: verify_ip_renew(self)
            },
            "flush_dns": {
                "name": "Flush DNS Cache",
                "risk": "low",
                "description": "Clears the DNS resolver cache.",
                "requires_admin": False,
                "execute": lambda: run_cmd("ipconfig /flushdns"),
                "verify": lambda: verify_dns_flush(self)
            },
            "restart_audio": {
                "name": "Restart Audio Service",
                "risk": "low",
                "description": "Restarts the Windows Audio service.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name AudioSrv -Force"),
                "verify": lambda: verify_audio_services(self)
            },
            "restart_bluetooth": {
                "name": "Restart Bluetooth Service",
                "risk": "low",
                "description": "Restarts the Windows Bluetooth Support service.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name bthserv -Force"),
                "verify": lambda: verify_service_status("bthserv", "Bluetooth Support Service", engine=self, repair_id="restart_bluetooth")
            },
            "enable_camera": {
                "name": "Enable Camera Device",
                "risk": "low",
                "description": "Attempts to enable the camera device using PnP.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Get-PnpDevice -Class Camera, Image -Status Error | Enable-PnpDevice -Confirm:$false"),
                "verify": lambda: verify_camera_pnp(self)
            },
            "restart_spooler": {
                "name": "Restart Print Spooler",
                "risk": "low",
                "description": "Restarts the Windows Print Spooler service.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name Spooler -Force"),
                "verify": lambda: verify_service_status("Spooler", "Print Spooler Service", engine=self, repair_id="restart_spooler")
            },
            "restart_wuauserv": {
                "name": "Restart Windows Update Service",
                "risk": "low",
                "description": "Restarts the Windows Update service to fix stuck updates.",
                "requires_admin": True,
                "execute": lambda: run_cmd("Restart-Service -Name wuauserv -Force"),
                "verify": lambda: verify_wuauserv_service(self)
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
            self.last_verification_error = str(e)
            return RepairState.VERIFICATION_FAILED
