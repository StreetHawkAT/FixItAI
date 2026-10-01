import subprocess
import json

def run_ps(cmd):
    try:
        result = subprocess.check_output(
            ["powershell", "-Command", cmd],
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.strip()
    except subprocess.CalledProcessError as e:
        return ""

def check_network():
    ping_res = run_ps("Test-Connection -ComputerName 8.8.8.8 -Count 1 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Status")
    internet_connected = (ping_res.strip().lower() == "success")

    adapters_json = run_ps("Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, MacAddress | ConvertTo-Json -Compress")
    adapters = []
    if adapters_json:
        try:
            adapters = json.loads(adapters_json)
            if isinstance(adapters, dict): adapters = [adapters]
        except:
            pass

    wifi_present = any("wi-fi" in str(a.get("Name", "")).lower() for a in adapters)
    ethernet_present = any("ethernet" in str(a.get("Name", "")).lower() for a in adapters)
    
    wifi_enabled = any("wi-fi" in str(a.get("Name", "")).lower() and str(a.get("Status", "")).lower() == "up" for a in adapters)

    wlan_svc = run_ps("(Get-Service -Name WlanSvc -ErrorAction SilentlyContinue).Status")

    ipconfig = run_ps("ipconfig")

    evidence = []
    if internet_connected:
        evidence.append("Internet connectivity verified (ping 8.8.8.8 succeeded).")
    else:
        evidence.append("Internet gateway ping test failed (8.8.8.8 unreachable).")

    if wifi_present:
        evidence.append(f"Wi-Fi adapter detected: Status {'Up' if wifi_enabled else 'Disabled/Down'}")
    else:
        evidence.append("Wi-Fi adapter not detected.")

    if ethernet_present:
        evidence.append("Ethernet adapter detected.")

    if wlan_svc:
        evidence.append(f"WLAN AutoConfig service (WlanSvc): {wlan_svc}")

    dhcp_failed = "169.254." in ipconfig
    if dhcp_failed:
        evidence.append("APIPA autoconfiguration IPv4 address (169.254.x.x) detected - DHCP lease failed.")

    # Try to find driver errors from PNP devices
    pnp_errors = run_ps("Get-PnpDevice -Class Net -Status Error | Select-Object FriendlyName, Status | ConvertTo-Json -Compress")
    driver_status = "ok"
    if pnp_errors and len(pnp_errors) > 5:
        driver_status = "error"
        evidence.append("Network adapter driver reporting PnP error.")

    status = "healthy" if (wifi_present and wifi_enabled and internet_connected) else "problem"
    if driver_status == "error":
        status = "problem"

    return {
        "category": "network",
        "status": status,
        "internet_connected": internet_connected,
        "wifi_present": wifi_present,
        "wifi_enabled": wifi_enabled,
        "ethernet_present": ethernet_present,
        "driver_status": driver_status,
        "wlan_service": wlan_svc,
        "dhcp_failed": dhcp_failed,
        "adapters": adapters,
        "evidence": evidence,
        "ipconfig": ipconfig[:200] + "..." if len(ipconfig) > 200 else ipconfig
    }
