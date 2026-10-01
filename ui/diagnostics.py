import streamlit as st
import time
from diagnostics.network import check_network
from diagnostics.crash import check_crashes
from diagnostics.camera import check_camera
from diagnostics.audio import check_audio
from diagnostics.bluetooth import check_bluetooth
from diagnostics.display import check_display
from diagnostics.keyboard import check_keyboard
from diagnostics.input_devices import check_input
from diagnostics.microphone import check_microphone
from diagnostics.usb import check_usb
from diagnostics.printer import check_printer
from diagnostics.battery import check_battery
from diagnostics.storage import check_storage
from diagnostics.performance import check_performance
from diagnostics.drivers import check_drivers
from diagnostics.windows import check_windows

DIAGNOSTIC_MODULES = {
    "network": check_network,
    "crash": check_crashes,
    "camera": check_camera,
    "audio": check_audio,
    "bluetooth": check_bluetooth,
    "display": check_display,
    "keyboard": check_keyboard,
    "mouse": check_input,
    "microphone": check_microphone,
    "usb": check_usb,
    "printer": check_printer,
    "battery": check_battery,
    "storage": check_storage,
    "performance": check_performance,
    "drivers": check_drivers,
    "windows": check_windows
}

def render_diagnostics():
    st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>WHAT'S WRONG?</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9ca3af;'>Tell FixIt AI what stopped working, or let it find out.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    categories = [
        {"id": "network", "icon": "🌐", "title": "Network", "sub": "Internet & adapters"},
        {"id": "audio", "icon": "🔊", "title": "Audio", "sub": "Sound & microphones"},
        {"id": "bluetooth", "icon": "ᛒ", "title": "Bluetooth", "sub": "Devices & connections"},
        {"id": "display", "icon": "🖥", "title": "Display", "sub": "Screens & graphics"},
        {"id": "keyboard", "icon": "⌨", "title": "Keyboard", "sub": "Keys & input"},
        {"id": "mouse", "icon": "🖱", "title": "Mouse / Touchpad", "sub": "Cursors & clicks"},
        {"id": "camera", "icon": "📷", "title": "Camera", "sub": "Video & webcams"},
        {"id": "microphone", "icon": "🎙", "title": "Microphone", "sub": "Voice & input"},
        {"id": "usb", "icon": "🔌", "title": "USB", "sub": "Ports & drives"},
        {"id": "printer", "icon": "🖨", "title": "Printer", "sub": "Spoolers & queues"},
        {"id": "battery", "icon": "🔋", "title": "Battery", "sub": "Power & charging"},
        {"id": "storage", "icon": "💾", "title": "Storage", "sub": "Drives & space"},
        {"id": "performance", "icon": "⚡", "title": "Performance", "sub": "Speed & freezes"},
        {"id": "drivers", "icon": "⚙", "title": "Drivers", "sub": "Devices & errors"},
        {"id": "windows", "icon": "🪟", "title": "Windows", "sub": "Updates & services"},
        {"id": "crash", "icon": "⚠", "title": "Crash", "sub": "Blue screens"}
    ]
    
    for i in range(0, len(categories), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(categories):
                cat = categories[i+j]
                with cols[j]:
                    with st.container(border=True):
                        st.markdown(f"""
                            <div style='text-align: center;'>
                                <div style='font-size: 2rem; margin-bottom: 5px;'>{cat['icon']}</div>
                                <div style='font-weight: 600; font-size: 1rem; margin-bottom: 2px;'>{cat['title']}</div>
                                <div style='font-size: 0.8rem; color: #9ca3af; margin-bottom: 15px;'>{cat['sub']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button("Check", key=f"cat_{cat['id']}", use_container_width=True):
                            run_category_scan(cat['id'])
                        
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("FULL LAPTOP DIAGNOSIS", type="primary", use_container_width=True):
            run_full_diagnosis()
            
    st.markdown("---")
    
    with st.expander("OFFLINE DEMO MODE (Simulated Diagnostic Data)"):
        st.write("No changes will be made to this computer. Use these to test the AI pipeline.")
        test_scenario = st.selectbox("Select Scenario", [
            "Camera: Multi-device (ASUS IR OK, FHD Error)",
            "Camera: Disabled (Code 22)",
            "Camera: Missing (0 detected)",
            "Camera: Privacy blocked",
            "Network: Wi-Fi disabled",
            "Network: DHCP failure",
            "Network: Driver error",
            "Audio: Service stopped",
            "Audio: Device missing",
            "Bluetooth: Driver error",
            "Bluetooth: Service stopped",
            "Display: Monitor not detected",
            "Keyboard: Disabled",
            "Mouse: Missing",
            "Microphone: Disabled",
            "USB: Device error",
            "Printer: Spooler stopped",
            "Battery: Not charging",
            "Storage: Low disk space",
            "Performance: High CPU",
            "Drivers: Device driver error",
            "Windows: Service stopped",
            "Crash: Unexpected shutdown"
        ])
        
        if st.button("Inject Offline Demo Scenario", use_container_width=True):
            inject_demo(test_scenario)

def run_category_scan(cat_id):
    with st.spinner(f"Analyzing {cat_id}..."):
        # Clear previous result explicitly as requested
        st.session_state['last_diagnosis'] = None
        
        func = DIAGNOSTIC_MODULES.get(cat_id)
        if func:
            try:
                res = func()
            except Exception as e:
                res = {"category": cat_id, "status": "unknown", "evidence": [f"Diagnostic failed to execute: {str(e)}"]}
        else:
            time.sleep(0.5)
            res = {"category": cat_id, "status": "unavailable", "evidence": ["Diagnostic module not yet implemented for this category."]}
            
        st.session_state['last_diagnosis'] = res
        st.session_state['diagnosis_type'] = f"{cat_id}_real"
        st.session_state["nav_page"] = "Troubleshoot"
        st.rerun()

def run_full_diagnosis():
    with st.spinner("Running full system diagnosis..."):
        st.session_state['last_diagnosis'] = None
        
        results = []
        for cat, func in DIAGNOSTIC_MODULES.items():
            try:
                res = func()
                results.append(res)
            except:
                pass
                
        # Find the first one with a problem to prioritize
        problem = next((r for r in results if r.get("status") == "problem"), None)
        
        if problem:
            res = problem
        else:
            res = next((r for r in results if r.get("category") == "network"), results[0])
            
        st.session_state['last_diagnosis'] = res
        st.session_state['diagnosis_type'] = "full_real"
        st.session_state["nav_page"] = "Troubleshoot"
        st.rerun()

def inject_demo(scenario):
    st.session_state['last_diagnosis'] = None
    data = {"category": scenario.split(":")[0].lower().replace(" ", "_"), "status": "problem"}
    
    if "Camera: Multi-device" in scenario:
        data = {
            "category": "camera", "status": "problem",
            "camera_present": True, "camera_enabled": True,
            "driver_status": "error", "device_status": "partial_error",
            "total_cameras": 2, "healthy_cameras": ["ASUS IR camera"],
            "problem_cameras": ["ASUS FHD webcam"],
            "devices": [
                {"Name": "ASUS IR camera", "Status": "OK", "Present": True, "Problem": 0, "ProblemDescription": "This device is working properly."},
                {"Name": "ASUS FHD webcam", "Status": "Error", "Present": True, "Problem": 10, "ProblemDescription": "This device cannot start. (Code 10)."}
            ],
            "frame_server_service": "Running", "privacy_access": "Allow",
            "evidence": [
                "Detected 2 camera/imaging device(s).",
                "Device: ASUS IR camera | Status: OK | PnP Code: 0 (This device is working properly.)",
                "Device: ASUS FHD webcam | Status: Error | PnP Code: 10 (This device cannot start. (Code 10).)",
                "Windows Camera Frame Server service: Running",
                "Windows Camera Privacy setting: Allow"
            ]
        }
    elif "Camera: Disabled" in scenario:
        data = {
            "category": "camera", "status": "problem",
            "camera_present": True, "camera_enabled": False,
            "driver_status": "ok", "device_status": "disabled",
            "total_cameras": 1, "disabled_cameras": ["Integrated Camera"],
            "devices": [
                {"Name": "Integrated Camera", "Status": "Error", "Present": True, "Problem": 22, "ProblemDescription": "This device is disabled. (Code 22)."}
            ],
            "frame_server_service": "Running", "privacy_access": "Allow",
            "evidence": [
                "Detected 1 camera/imaging device(s).",
                "Device: Integrated Camera | Status: Error | PnP Code: 22 (This device is disabled. (Code 22).)",
                "Windows Camera Frame Server service: Running",
                "Windows Camera Privacy setting: Allow"
            ]
        }
    elif "Camera: Missing" in scenario:
        data = {
            "category": "camera", "status": "problem",
            "camera_present": False, "total_cameras": 0, "devices": [],
            "evidence": ["No camera device was detected by Windows."]
        }
    elif "Camera: Privacy blocked" in scenario:
        data = {
            "category": "camera", "status": "problem",
            "camera_present": True, "camera_enabled": True,
            "privacy_access": "Deny", "frame_server_service": "Running",
            "devices": [
                {"Name": "Integrated Camera", "Status": "OK", "Present": True, "Problem": 0, "ProblemDescription": "This device is working properly."}
            ],
            "evidence": [
                "Detected 1 camera/imaging device(s).",
                "Device: Integrated Camera | Status: OK",
                "Windows Camera Privacy setting: Deny"
            ]
        }
    elif "Network" in scenario:
        data = {
            "category": "network", "status": "problem", "internet_connected": False,
            "wifi_present": True, "wifi_enabled": True, "ethernet_present": False,
            "driver_status": "ok", "wlan_service": "running", "evidence": ["Simulated network problem."]
        }
        if "Wi-Fi disabled" in scenario: data["wifi_enabled"] = False
        elif "Driver error" in scenario: data["driver_status"] = "error"
    elif "Audio" in scenario:
        data["category"] = "audio"
        data["evidence"] = ["Audio scenario triggered."]
        if "Service stopped" in scenario: data["service_running"] = False
    elif "Bluetooth" in scenario:
        data["category"] = "bluetooth"
        data["evidence"] = ["Bluetooth error simulated."]
        if "Service stopped" in scenario:
            data["service_running"] = False
            data["driver_status"] = "ok"
        else:
            data["driver_status"] = "error"
    else:
        data["evidence"] = [f"Simulated offline issue for {scenario}"]
        
    st.session_state['last_diagnosis'] = data
    st.session_state['diagnosis_type'] = "demo_test"
    st.session_state["nav_page"] = "Troubleshoot"
    st.rerun()
