import os

files = {
    "core/hardware_detection.py": """
import platform
import subprocess

def detect_hardware():
    arch = platform.machine().lower()
    is_arm = 'arm' in arch or 'aarch64' in arch
    
    # Try to get processor name via WMI
    processor = "Unknown"
    try:
        output = subprocess.check_output(
            ["powershell", "-Command", "(Get-WmiObject Win32_Processor).Name"],
            text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        processor = output.strip()
    except:
        pass
        
    is_snapdragon = "snapdragon" in processor.lower()
    
    return {
        "architecture": "ARM64" if is_arm else "x64" if "amd64" in arch else arch,
        "processor": processor,
        "is_snapdragon": is_snapdragon,
        "npu_available": is_snapdragon  # Simplification for demo
    }
""",

    "core/safety_manager.py": """
import logging

class SafetyManager:
    def __init__(self):
        self.log = logging.getLogger("SafetyManager")
        
    def verify_safe_to_execute(self, repair_id):
        return True
""",

    "diagnostics/network.py": """
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

    return {
        "internet_connected": internet_connected,
        "wifi_present": wifi_present,
        "wifi_enabled": wifi_enabled,
        "ethernet_present": ethernet_present,
        "wlan_service": wlan_svc,
        "adapters": adapters,
        "ipconfig": ipconfig[:200] + "..." if len(ipconfig) > 200 else ipconfig
    }
""",

    "diagnostics/crash.py": """
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
            return {"recent_crashes": []}
        data = json.loads(result)
        if isinstance(data, dict): data = [data]
        return {"recent_crashes": data}
    except:
        return {"recent_crashes": []}
""",

    "core/ai_engine.py": """
class LocalAIEngine:
    def __init__(self):
        self.is_ready = True
        
    def is_available(self):
        return self.is_ready
        
    def explain_diagnosis(self, diagnosis_data):
        if not diagnosis_data.get("internet_connected"):
            if diagnosis_data.get("wifi_present") and not diagnosis_data.get("wifi_enabled"):
                return "The Wi-Fi adapter is present but disabled. Enabling it should restore connectivity."
            elif not diagnosis_data.get("wifi_present") and diagnosis_data.get("wlan_service", "").lower() != "running":
                return "The WLAN AutoConfig service is not running, which is required for Wi-Fi. Restarting it may help."
            else:
                return "Your network adapter is facing an issue. A network reset or DHCP release/renew might resolve the problem."
        
        crashes = diagnosis_data.get("recent_crashes", [])
        if crashes:
            return "You had recent system crashes. This may have caused driver instability."

        return "Your system seems generally healthy, but some minor issues may be present."
""",

    "core/repair_engine.py": """
import subprocess

class RepairEngine:
    def __init__(self):
        self.repairs = {
            "enable_wifi": {
                "name": "Enable Wi-Fi Adapter",
                "risk": "Low",
                "description": "Enables the disabled Wi-Fi adapter.",
                "cmd": "Enable-NetAdapter -Name 'Wi-Fi' -Confirm:$false"
            },
            "restart_wlan": {
                "name": "Restart WLAN Service",
                "risk": "Low",
                "description": "Restarts the Windows wireless service.",
                "cmd": "Restart-Service -Name WlanSvc -Force"
            },
            "ip_renew": {
                "name": "Renew IP Address",
                "risk": "Low",
                "description": "Releases and renews your IP address from the DHCP server.",
                "cmd": "ipconfig /release; ipconfig /renew"
            }
        }
        
    def get_available_repairs(self):
        return self.repairs
        
    def execute_repair(self, repair_id):
        repair = self.repairs.get(repair_id)
        if not repair:
            return False, "Repair not found"
            
        try:
            subprocess.check_output(["powershell", "-Command", repair["cmd"]], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return True, "Repair executed successfully."
        except subprocess.CalledProcessError as e:
            return False, f"Failed to execute: {e}"
""",

    "ui/dashboard.py": """
import streamlit as st
from core.hardware_detection import detect_hardware

def render_dashboard():
    st.title("FixIt AI - Dashboard")
    st.markdown("Welcome to FixIt AI, your offline-first Windows troubleshooting assistant.")
    
    hw = detect_hardware()
    st.subheader("Hardware Information")
    st.write(f"**Architecture:** {hw['architecture']}")
    st.write(f"**Processor:** {hw['processor']}")
    if hw['is_snapdragon']:
        st.success("Snapdragon NPU acceleration available.")
    else:
        st.info("Snapdragon acceleration unavailable. CPU inference active.")
""",

    "ui/diagnostics.py": """
import streamlit as st
from diagnostics.network import check_network
from diagnostics.crash import check_crashes
from core.ai_engine import LocalAIEngine

def render_diagnostics():
    st.title("Diagnostics")
    
    col1, col2 = st.columns(2)
    
    if col1.button("Run Network Diagnosis"):
        with st.spinner("Analyzing network..."):
            net_res = check_network()
            st.session_state['last_diagnosis'] = net_res
            st.session_state['diagnosis_type'] = "network"
            st.success("Network Diagnosis Complete!")
            
    if col2.button("Run Crash Diagnosis"):
        with st.spinner("Analyzing recent crashes..."):
            crash_res = check_crashes()
            st.session_state['last_diagnosis'] = crash_res
            st.session_state['diagnosis_type'] = "crash"
            st.success("Crash Diagnosis Complete!")
            
    if 'last_diagnosis' in st.session_state:
        st.subheader("Raw Diagnostic Data")
        st.json(st.session_state['last_diagnosis'])
        
        st.subheader("AI Explanation")
        ai = LocalAIEngine()
        explanation = ai.explain_diagnosis(st.session_state['last_diagnosis'])
        st.info(explanation)
""",

    "ui/troubleshooting.py": """
import streamlit as st
from core.repair_engine import RepairEngine
from diagnostics.network import check_network

def render_troubleshooting():
    st.title("Troubleshooting & Repairs")
    
    engine = RepairEngine()
    repairs = engine.get_available_repairs()
    
    for r_id, r_info in repairs.items():
        with st.expander(f"{r_info['name']} (Risk: {r_info['risk']})"):
            st.write(r_info['description'])
            if st.button(f"Execute {r_info['name']}", key=r_id):
                with st.spinner("Executing repair..."):
                    success, msg = engine.execute_repair(r_id)
                    if success:
                        st.success(msg)
                        st.info("Verifying network state...")
                        net_res = check_network()
                        if net_res['internet_connected']:
                            st.success("Verification: Internet is connected!")
                        else:
                            st.warning("Verification: Internet is still disconnected.")
                    else:
                        st.error(msg)
""",

    "app.py": """
import streamlit as st
from ui.dashboard import render_dashboard
from ui.diagnostics import render_diagnostics
from ui.troubleshooting import render_troubleshooting

st.set_page_config(page_title="FixIt AI", layout="wide")

st.sidebar.title("FixIt AI")
page = st.sidebar.radio("Navigation", ["Dashboard", "Diagnostics", "Troubleshooting"])

if page == "Dashboard":
    render_dashboard()
elif page == "Diagnostics":
    render_diagnostics()
elif page == "Troubleshooting":
    render_troubleshooting()
"""
}

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Created {filepath}")

