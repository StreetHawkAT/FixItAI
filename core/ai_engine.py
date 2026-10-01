import json
import urllib.request
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class InferenceBackend:
    def generate(self, data):
        raise NotImplementedError

class RuleBasedBackend(InferenceBackend):
    def generate(self, data):
        status = data.get("status", "unknown")
        cat = str(data.get("category", "")).lower()
        
        if status == "unavailable":
            return {
                "summary": "Diagnostic Unavailable.",
                "problem": "Diagnostic module is not implemented for this category.",
                "likely_causes": ["Diagnostic module not yet implemented or supported on this system."],
                "evidence": data.get("evidence", ["Diagnostic module not yet implemented for this category."]),
                "confidence": "HIGH",
                "why": "No diagnostic script is registered for this category.",
                "recommended_action": "Check system manually via Windows Device Manager or Settings.",
                "action_type": "user_action",
                "user_steps": [
                    "Open Windows Device Manager (devmgmt.msc).",
                    "Inspect the relevant device category for warning icons or missing devices."
                ],
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True,
                "verification_plan": "Not applicable.",
                "fallback_action": "Consult hardware documentation or contact device support."
            }
            
        if status == "unknown":
            return {
                "summary": "Windows diagnostic command failed.",
                "problem": "Windows diagnostic command failed to retrieve telemetry.",
                "likely_causes": ["PowerShell or WMI execution timed out, was restricted by policy, or returned malformed output."],
                "evidence": data.get("evidence", ["Diagnostic execution failure."]),
                "confidence": "HIGH",
                "why": "Windows diagnostic command failed to return valid telemetry data.",
                "recommended_action": "Restart FixIt AI as Administrator and retry the diagnostic.",
                "action_type": "user_action",
                "user_steps": [
                    "Close FixIt AI.",
                    "Right-click PowerShell or your terminal and select 'Run as administrator'.",
                    "Re-launch FixIt AI and retry the diagnostic scan."
                ],
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True,
                "verification_plan": "Not applicable.",
                "fallback_action": "Check Windows PowerShell execution policy using 'Get-ExecutionPolicy'."
            }

        if status == "healthy":
            return {
                "summary": "System functioning normally.",
                "problem": f"{cat.capitalize()} subsystem is functioning normally.",
                "likely_causes": ["All diagnostic checks and service states are healthy."],
                "evidence": data.get("evidence", [f"{cat.capitalize()} checks passed."]),
                "confidence": "HIGH",
                "why": "Windows telemetry confirms all devices and services in this subsystem report healthy status.",
                "recommended_action": "No repair needed.",
                "action_type": "none",
                "user_steps": [],
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": False,
                "verification_plan": "Subsystem is currently operating within normal parameters.",
                "fallback_action": "Run specific diagnostics if intermittent issues occur."
            }

        # Handle problems by category
        if cat == "camera":
            devices = data.get("devices", [])
            total_cameras = data.get("total_cameras", len(devices))
            healthy_cameras = data.get("healthy_cameras", [])
            disabled_cameras = data.get("disabled_cameras", [])
            problem_cameras = data.get("problem_cameras", [])
            frame_server = str(data.get("frame_server_service", "")).lower()
            privacy = str(data.get("privacy_access", "")).lower()
            evidence = data.get("evidence", [])

            # Check if insufficient evidence provided (no devices and camera_present not explicitly specified)
            if not devices and "camera_present" not in data:
                return {
                    "summary": "Camera issue detected but specific cause is unknown.",
                    "problem": "Camera issue detected but specific cause could not be isolated from available telemetry.",
                    "likely_causes": ["System reports an issue with the camera subsystem."],
                    "evidence": evidence if evidence else ["Insufficient telemetry data provided."],
                    "confidence": "LOW",
                    "why": "No camera telemetry or device nodes were provided to isolate the failure.",
                    "recommended_action": "Run a full camera diagnostic to capture device status.",
                    "action_type": "user_action",
                    "user_steps": [
                        "1. Open Device Manager → Cameras.",
                        "2. Check whether camera hardware is listed.",
                        "3. Restart the PC."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "Inspect hardware connections or contact support."
                }

            # Check if camera not present (explicitly marked False or 0 cameras detected with camera_present in data)
            if data.get("camera_present") is False or (total_cameras == 0 and data.get("camera_present") is not True):
                return {
                    "summary": "Windows could not detect a camera device.",
                    "problem": "No camera or imaging hardware detected by Windows.",
                    "likely_causes": [
                        "Physical privacy shutter or kill switch is active.",
                        "Camera is disabled in laptop BIOS/UEFI firmware.",
                        "Missing camera / USB bus driver preventing device enumeration.",
                        "Hardware ribbon cable disconnection."
                    ],
                    "evidence": evidence if evidence else ["0 camera/imaging devices enumerated in Windows PnP."],
                    "confidence": "HIGH",
                    "why": "Windows PnP returned zero devices in Camera and Image device classes.",
                    "recommended_action": "Check physical privacy shutter, keyboard camera hotkey, and BIOS settings.",
                    "action_type": "user_action",
                    "user_steps": [
                        "1. Inspect the top bezel above your screen for a sliding physical privacy shutter.",
                        "2. Check keyboard function keys for a camera toggle (e.g. Fn + F10 or Fn + F6).",
                        "3. Restart PC, press F2/Del at startup to enter BIOS/UEFI, and verify Integrated Camera is Enabled.",
                        "4. Open Device Manager (devmgmt.msc) and check 'Other devices' for unknown devices."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "If camera remains undetected across reboots, hardware inspection or manufacturer service is justified."
                }

            # Check if Windows privacy is blocking camera access
            if privacy == "deny":
                return {
                    "summary": "Camera access is blocked by Windows Privacy settings.",
                    "problem": "Windows Privacy settings are preventing applications from accessing the camera.",
                    "likely_causes": ["Camera access is toggled OFF in Windows Settings."],
                    "evidence": evidence,
                    "confidence": "HIGH",
                    "why": "Windows CapabilityAccessManager ConsentStore reports camera access is set to Deny.",
                    "recommended_action": "Enable camera access in Windows Settings.",
                    "action_type": "user_action",
                    "user_steps": [
                        "1. Press Win + I to open Windows Settings.",
                        "2. Navigate to Privacy & security → Camera.",
                        "3. Turn ON 'Camera access' and 'Let desktop apps access your camera'."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "Check for third-party privacy software (e.g. Lenovo Vantage, ASUS Armoury Crate) that may also control camera access."
                }

            # Check if FrameServer service is stopped
            if frame_server == "stopped":
                return {
                    "summary": "Windows Camera Frame Server service is stopped.",
                    "problem": "Windows Camera Frame Server service (FrameServer) is not running.",
                    "likely_causes": ["The FrameServer service was stopped or failed to start."],
                    "evidence": evidence,
                    "confidence": "HIGH",
                    "why": "Windows Service Manager reports FrameServer service status is Stopped.",
                    "recommended_action": "Start the Windows Camera Frame Server service in services.msc.",
                    "action_type": "user_action",
                    "user_steps": [
                        "1. Press Win + R, type services.msc, and press Enter.",
                        "2. Locate 'Windows Camera Frame Server'.",
                        "3. Right-click it and select 'Start', and set Startup type to 'Automatic'."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "If service crashes immediately upon starting, check Windows Event Viewer System log for crash codes."
                }

            # Check if camera is disabled (Code 22 or explicitly disabled)
            has_disabled = len(disabled_cameras) > 0 or data.get("device_status") == "disabled"
            if not has_disabled and devices:
                for d in devices:
                    p = d.get("Problem")
                    pd = str(d.get("ProblemDescription", "")).lower()
                    if p == 22 or "disabled" in pd or str(d.get("Status")).upper() == "DISABLED":
                        has_disabled = True
                        break

            if has_disabled:
                dev_label = disabled_cameras[0] if disabled_cameras else "Camera device"
                if healthy_cameras:
                    problem_desc = f"FixIt AI detected {len(devices)} camera devices: {', '.join(healthy_cameras)} is operational, while {dev_label} is currently disabled."
                else:
                    problem_desc = f"Windows detected {dev_label}, but the device is disabled."

                return {
                    "summary": "Windows detected the camera, but the device is disabled.",
                    "problem": problem_desc,
                    "likely_causes": [
                        "The camera was disabled in Windows Device Manager.",
                        "Device was disabled by system policy or a device management utility."
                    ],
                    "evidence": evidence,
                    "confidence": "HIGH",
                    "why": "Windows PnP subsystem explicitly reports Problem Code 22 (CM_PROB_DISABLED), indicating the device is present and enumerated but disabled.",
                    "recommended_action": "Re-enable the camera device using FixIt AI's safe automated repair.",
                    "action_type": "automated_repair",
                    "user_steps": [
                        "Click 'RUN REPAIR' below to enable the device.",
                        "Alternatively, open Device Manager → Cameras, right-click the device, and select 'Enable device'."
                    ],
                    "repair_id": "enable_camera",
                    "repair_reason": "Enabling the camera via PnP will instruct Windows to re-activate the device.",
                    "risk": "low",
                    "cannot_fix": False,
                    "verification_plan": "FixIt AI will re-query the PnP state of Camera devices to verify Windows reports status OK.",
                    "fallback_action": "If the camera does not re-enable, open Device Manager → Cameras, right-click the device, and select 'Enable device'. If blocked by a hardware switch, toggle the camera privacy switch or Fn hotkey."
                }

            # Multi-camera scenario: One camera OK + one camera ERROR
            if healthy_cameras and (problem_cameras or data.get("driver_status") == "error"):
                prob_names = [d if isinstance(d, str) else d.get("Name", "Webcam") for d in problem_cameras]
                if not prob_names:
                    prob_names = [d.get("Name", "Webcam") for d in devices if str(d.get("Status")).upper() != "OK"]
                prob_label = ", ".join(prob_names) if prob_names else "secondary webcam"
                healthy_label = ", ".join(healthy_cameras)

                return {
                    "summary": f"Windows detected multiple camera devices with an error isolated to {prob_label}.",
                    "problem": f"FixIt AI detected {len(devices)} camera devices. The {healthy_label} is reporting OK, while the {prob_label} is reporting an error.",
                    "likely_causes": [
                        f"Device Manager / PnP error state on {prob_label}.",
                        "Camera driver communication timeout or initialization failure.",
                        "Application exclusivity conflict (another application holding exclusive access).",
                        "Hardware connection or firmware state if Windows reports a persistent hardware error."
                    ],
                    "evidence": evidence,
                    "confidence": "MEDIUM",
                    "why": f"Windows can enumerate {prob_label}, but the device is not currently functioning normally. Because {healthy_label} is healthy and camera services are operating, this issue is isolated to {prob_label} rather than a complete Windows camera subsystem failure. The available telemetry confirms a device-level error, but does not prove driver corruption.",
                    "recommended_action": "Investigate Device Manager error code, camera permissions, and application exclusivity.",
                    "action_type": "user_action",
                    "user_steps": [
                        f"1. Open Device Manager (devmgmt.msc) and expand 'Cameras'.",
                        f"2. Right-click {prob_label} and select Properties to inspect the Device Status error code.",
                        "3. Check Windows Settings → Privacy & security → Camera to ensure camera access is ON.",
                        "4. Close applications (Teams, Zoom, browser) that might currently hold exclusive access to the webcam.",
                        "5. Restart your PC to clear temporary driver or controller lockups."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": f"If Device Manager reports a persistent Code 10 or Code 43 on {prob_label} after restarting and reinstalling the official manufacturer driver, hardware inspection of the webcam module is justified."
                }

            # Single camera reporting ERROR / PnP error
            if data.get("driver_status") == "error" or data.get("device_status") == "error" or problem_cameras:
                cam_name = devices[0].get("Name", "Camera") if devices else "Camera"
                prob_code = devices[0].get("Problem") if devices else None
                prob_desc = devices[0].get("ProblemDescription") if devices else None
                has_code = prob_code is not None and prob_code != 0

                confidence = "MEDIUM" if has_code else "LOW"
                why_text = f"Windows PnP reports device status Error"
                if has_code and prob_desc:
                    why_text += f" with Problem Code {prob_code} ({prob_desc})."
                else:
                    why_text += ". Telemetry confirms a device error, but cannot confirm driver corruption without further diagnostics."

                return {
                    "summary": "Windows detected the camera, but the device is reporting a driver or device error.",
                    "problem": f"Camera device '{cam_name}' is reporting a Windows PnP device error.",
                    "likely_causes": [
                        "Device startup error or driver initialization failure.",
                        "Application exclusivity conflict (another application holding camera access).",
                        "Camera hardware communication failure."
                    ],
                    "evidence": evidence,
                    "confidence": confidence,
                    "why": why_text,
                    "recommended_action": "Check Device Manager error code, privacy permissions, and close background camera apps.",
                    "action_type": "user_action",
                    "user_steps": [
                        "1. Open Device Manager (devmgmt.msc) and expand 'Cameras'.",
                        f"2. Right-click {cam_name} and select Properties to check the Device Status error code.",
                        "3. Check Windows Settings → Privacy & security → Camera.",
                        "4. Close all applications that may be using the camera (Zoom, Teams, browser).",
                        "5. Restart your PC."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "If the error persists after rebooting, reinstall the manufacturer's camera driver. If the device remains in error, hardware service is justified."
                }

            # Generic camera problem fallback
            return {
                "summary": "Camera issue detected but specific cause is unknown.",
                "problem": "Camera issue detected but specific cause could not be isolated from available telemetry.",
                "likely_causes": ["System reports an issue with the camera subsystem."],
                "evidence": evidence,
                "confidence": "LOW",
                "why": "Telemetry indicates an issue but does not provide specific PnP problem codes.",
                "recommended_action": "Open Device Manager and verify camera hardware status.",
                "action_type": "user_action",
                "user_steps": [
                    "Open Device Manager → Cameras.",
                    "Check device status and error codes.",
                    "Restart the PC."
                ],
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True,
                "verification_plan": "Not applicable.",
                "fallback_action": "Inspect hardware connections or contact support."
            }

        elif cat == "network":
            evidence = data.get("evidence", [])
            if not evidence:
                if data.get("wifi_present"): evidence.append("Wi-Fi adapter detected")
                else: evidence.append("Wi-Fi adapter not found")
                
                if data.get("wifi_enabled"): evidence.append("Adapter enabled")
                elif data.get("wifi_present"): evidence.append("Adapter disabled")
                
                if str(data.get("wlan_service", "")).lower() == "running":
                    evidence.append("WLAN service running")
                else:
                    evidence.append("WLAN service stopped")

            if not data.get("internet_connected"):
                if data.get("wlan_service") and str(data.get("wlan_service")).lower() != "running":
                    return {
                        "summary": "Internet connection unavailable.",
                        "problem": "WLAN AutoConfig service is not running.",
                        "likely_causes": ["The WLAN AutoConfig service is not running."],
                        "evidence": evidence,
                        "confidence": "HIGH",
                        "why": "Windows Service Manager reports WlanSvc status is not Running.",
                        "recommended_action": "Start the WLAN AutoConfig service.",
                        "action_type": "automated_repair",
                        "user_steps": [
                            "Click 'RUN REPAIR' below to restart the WLAN service."
                        ],
                        "repair_id": "restart_wlan",
                        "repair_reason": "Starting the WLAN service is required for Wi-Fi.",
                        "risk": "low",
                        "cannot_fix": False,
                        "verification_plan": "FixIt AI will verify that Get-Service WlanSvc reports status 'Running'.",
                        "fallback_action": "Check service dependencies in services.msc (RPC service and Windows Event Log)."
                    }

                elif not data.get("wifi_present") and not data.get("ethernet_present"):
                    return {
                        "summary": "Internet connection unavailable.",
                        "problem": "No network adapters detected by Windows.",
                        "likely_causes": ["No network adapters are present."],
                        "evidence": evidence,
                        "confidence": "HIGH",
                        "why": "Windows reports no wireless or Ethernet adapters enumerated in the system.",
                        "recommended_action": "Check BIOS settings to verify onboard network controller is enabled.",
                        "action_type": "user_action",
                        "user_steps": [
                            "1. Restart the PC and enter BIOS/UEFI settings.",
                            "2. Ensure Integrated Wireless / LAN is enabled.",
                            "3. Open Device Manager and check 'Other devices' for missing network drivers."
                        ],
                        "repair_id": None,
                        "repair_reason": "",
                        "risk": "low",
                        "cannot_fix": True,
                        "verification_plan": "Not applicable.",
                        "fallback_action": "If network adapters are absent in BIOS, hardware service or a USB Wi-Fi adapter is required."
                    }

                elif data.get("driver_status") == "error":
                    return {
                        "summary": "Internet connection unavailable.",
                        "problem": "Network adapter is reporting a driver or PnP error.",
                        "likely_causes": ["Network driver is reporting an error."],
                        "evidence": evidence,
                        "confidence": "MEDIUM",
                        "why": "Windows PnP reports an error status for one or more network controllers.",
                        "recommended_action": "Inspect Device Manager for the network adapter error code and reinstall the driver.",
                        "action_type": "user_action",
                        "user_steps": [
                            "1. Open Device Manager → Network adapters.",
                            "2. Right-click your network adapter and check Properties for the error code.",
                            "3. Select 'Update driver' or rollback to previous driver.",
                            "4. Restart your PC."
                        ],
                        "repair_id": None,
                        "repair_reason": "",
                        "risk": "low",
                        "cannot_fix": True,
                        "verification_plan": "Not applicable.",
                        "fallback_action": "If Code 10/43 persists after a restart, reinstall the manufacturer's network driver."
                    }

                elif data.get("wifi_present") and not data.get("wifi_enabled"):
                    return {
                        "summary": "Internet connection unavailable.",
                        "problem": "Wi-Fi adapter is present but disabled.",
                        "likely_causes": ["The Wi-Fi adapter is present but disabled."],
                        "evidence": evidence,
                        "confidence": "HIGH",
                        "why": "Windows Network Adapter telemetry indicates the interface exists but its status is Down/Disabled.",
                        "recommended_action": "Enable the Wi-Fi adapter using FixIt AI's safe automated repair.",
                        "action_type": "automated_repair",
                        "user_steps": [
                            "Click 'RUN REPAIR' below to enable the Wi-Fi adapter.",
                            "Alternatively, go to Settings → Network & internet → Advanced network settings and enable Wi-Fi."
                        ],
                        "repair_id": "enable_wifi",
                        "repair_reason": "Enabling the adapter will restore connectivity.",
                        "risk": "low",
                        "cannot_fix": False,
                        "verification_plan": "FixIt AI will check Get-NetAdapter -Name 'Wi-Fi' to confirm status is 'Up'.",
                        "fallback_action": "If the adapter fails to come Up, check Windows Settings → Network & internet, or verify physical Wi-Fi switch / hotkey."
                    }

                elif not data.get("wifi_present") and str(data.get("wlan_service", "")).lower() != "running":
                    return {
                        "summary": "Internet connection unavailable.",
                        "problem": "WLAN AutoConfig service is not running.",
                        "likely_causes": ["The WLAN AutoConfig service is not running."],
                        "evidence": evidence,
                        "confidence": "HIGH",
                        "why": "Windows Service Manager reports WlanSvc status is not Running.",
                        "recommended_action": "Start the WLAN AutoConfig service.",
                        "action_type": "automated_repair",
                        "user_steps": [
                            "Click 'RUN REPAIR' below to restart the WLAN service."
                        ],
                        "repair_id": "restart_wlan",
                        "repair_reason": "Starting the WLAN service is required for Wi-Fi.",
                        "risk": "low",
                        "cannot_fix": False,
                        "verification_plan": "FixIt AI will verify that Get-Service WlanSvc reports status 'Running'.",
                        "fallback_action": "Check service dependencies in services.msc (RPC service and Windows Event Log)."
                    }

                else:
                    return {
                        "summary": "Internet connection unavailable.",
                        "problem": "Network configuration failed (DHCP or DNS issue).",
                        "likely_causes": ["Network configuration failed (DHCP/DNS issue)."],
                        "evidence": evidence,
                        "confidence": "MEDIUM",
                        "why": "Adapter is active and connected, but gateway ping failed or IP address lease is invalid.",
                        "recommended_action": "Release and renew the IP address from DHCP.",
                        "action_type": "automated_repair",
                        "user_steps": [
                            "Click 'RUN REPAIR' below to release and renew your IP address."
                        ],
                        "repair_id": "ip_renew",
                        "repair_reason": "Releasing and renewing IP can fix DHCP issues.",
                        "risk": "low",
                        "cannot_fix": False,
                        "verification_plan": "FixIt AI will execute a ping test to verify connectivity to 8.8.8.8.",
                        "fallback_action": "If renewing IP fails, power cycle your Wi-Fi router (unplug for 30 seconds) or test with a mobile hotspot."
                    }

        elif cat == "audio":
            evidence = data.get("evidence", [])
            service_running = data.get("service_running", True)
            driver_error = (data.get("driver_status") == "error")

            if not service_running:
                return {
                    "summary": "Windows Audio service is not running.",
                    "problem": "Windows Audio service (AudioSrv) is stopped.",
                    "likely_causes": ["The Windows Audio service was stopped or encountered a crash."],
                    "evidence": evidence if evidence else ["Audio device detected", "Service stopped"],
                    "confidence": "HIGH",
                    "why": "Windows Service Manager reports AudioSrv status is not Running.",
                    "recommended_action": "Restart the Windows Audio service.",
                    "action_type": "automated_repair",
                    "user_steps": ["Click 'RUN REPAIR' below to restart the Windows Audio service."],
                    "repair_id": "restart_audio",
                    "repair_reason": "Restarting the Windows Audio service.",
                    "risk": "low",
                    "cannot_fix": False,
                    "verification_plan": "FixIt AI will check Get-Service AudioSrv to confirm status is 'Running'.",
                    "fallback_action": "If AudioSrv stops again, check Windows Audio Endpoint Builder in services.msc."
                }

            elif driver_error:
                return {
                    "summary": "Audio device is reporting a driver or PnP error.",
                    "problem": "Audio media device is reporting a PnP error.",
                    "likely_causes": ["Audio device driver encountered an error or failed to start."],
                    "evidence": evidence,
                    "confidence": "MEDIUM",
                    "why": "Windows PnP reports Status Error on an audio media device. Telemetry does not prove driver corruption without further diagnostics.",
                    "recommended_action": "Scan for hardware changes in Device Manager and reinstall audio driver.",
                    "action_type": "user_action",
                    "user_steps": [
                        "1. Open Device Manager → Sound, video and game controllers.",
                        "2. Right-click your audio device (e.g. Realtek) and check Properties.",
                        "3. Select 'Update driver' or 'Uninstall device', then click 'Scan for hardware changes'.",
                        "4. Restart your PC."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "Download and install the official audio driver from your laptop manufacturer support portal."
                }

            elif not data.get("output_device_present", True):
                return {
                    "summary": "No audio devices detected.",
                    "problem": "No audio media devices detected by Windows.",
                    "likely_causes": ["Audio hardware is disconnected, disabled in BIOS, or missing drivers."],
                    "evidence": evidence,
                    "confidence": "HIGH",
                    "why": "Windows PnP enumerated 0 audio devices in the Media class.",
                    "recommended_action": "Check Device Manager and verify audio is enabled in BIOS.",
                    "action_type": "user_action",
                    "user_steps": [
                        "Check external speaker/headphone connections.",
                        "Verify onboard audio is enabled in BIOS/UEFI settings."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "Hardware inspection of audio codec / motherboard is justified if audio chip is undetected."
                }

        elif cat == "bluetooth":
            evidence = data.get("evidence", [])
            driver_error = (data.get("driver_status") == "error")
            service_running = data.get("service_running", True)

            if driver_error:
                return {
                    "summary": "Bluetooth driver is reporting an error.",
                    "problem": "Bluetooth adapter is reporting a driver or PnP device error.",
                    "likely_causes": ["The Bluetooth adapter driver encountered a device or initialization error."],
                    "evidence": evidence if evidence else ["Bluetooth adapter detected", "Driver reporting error"],
                    "confidence": "MEDIUM",
                    "why": "Windows PnP reports Status Error for the Bluetooth adapter. Telemetry confirms a device error, but does not prove driver corruption.",
                    "recommended_action": "Disable and re-enable Bluetooth in Device Manager, then reboot.",
                    "action_type": "user_action",
                    "user_steps": [
                        "1. Open Device Manager → Bluetooth.",
                        "2. Right-click your Bluetooth adapter (Intel, Realtek, Qualcomm) and select Properties.",
                        "3. Check the error code under Device Status.",
                        "4. Right-click and choose 'Disable device', wait 5 seconds, then 'Enable device'.",
                        "5. Restart your PC."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "If the Bluetooth adapter remains in error across reboots, reinstall the official Bluetooth driver."
                }

            elif not service_running:
                return {
                    "summary": "Bluetooth service is stopped.",
                    "problem": "Windows Bluetooth Support service (bthserv) is stopped.",
                    "likely_causes": ["The Bluetooth service was stopped or disabled."],
                    "evidence": evidence if evidence else ["Bluetooth adapter detected", "Service stopped"],
                    "confidence": "HIGH",
                    "why": "Windows Service Manager reports bthserv status is not Running.",
                    "recommended_action": "Restart the Bluetooth service.",
                    "action_type": "automated_repair",
                    "user_steps": ["Click 'RUN REPAIR' below to restart the Bluetooth service."],
                    "repair_id": "restart_bluetooth",
                    "repair_reason": "Restarting the service will enable connectivity.",
                    "risk": "low",
                    "cannot_fix": False,
                    "verification_plan": "FixIt AI will verify Get-Service bthserv reports status 'Running'.",
                    "fallback_action": "If service cannot start, check Bluetooth Audio Gateway Service and RPC service dependencies."
                }

            elif not data.get("bluetooth_present", True):
                return {
                    "summary": "No Bluetooth adapter detected.",
                    "problem": "No Bluetooth adapter detected by Windows.",
                    "likely_causes": ["Bluetooth is disabled via Fn hotkey, in BIOS, or adapter is missing."],
                    "evidence": evidence,
                    "confidence": "HIGH",
                    "why": "Windows PnP returned zero Bluetooth radio devices.",
                    "recommended_action": "Check keyboard Fn hotkey for Airplane mode and verify Bluetooth in BIOS.",
                    "action_type": "user_action",
                    "user_steps": [
                        "Check keyboard function keys for Airplane mode or Bluetooth toggle.",
                        "Restart PC and verify Bluetooth is enabled in BIOS/UEFI."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "If Bluetooth hardware is missing, use a USB Bluetooth dongle or service wireless module."
                }

        elif cat == "crash":
            crashes = data.get("recent_crashes", [])
            evidence = data.get("evidence", [])
            if not evidence and crashes:
                evidence = [f"Event ID {c.get('Id')} from {c.get('ProviderName')}" for c in crashes[:2]]
            
            return {
                "summary": f"Detected {len(crashes)} recent system crashes." if crashes else "System crash events logged.",
                "problem": f"Detected {len(crashes)} recent system crash or unexpected shutdown event(s)." if crashes else "System crash events logged.",
                "likely_causes": ["Recent unexpected power loss, kernel bugcheck, or driver crash."],
                "evidence": evidence if evidence else ["System crash event detected in Windows System Log."],
                "confidence": "MEDIUM",
                "why": "Windows System Event Log contains critical BugCheck or Kernel-Power failure events.",
                "recommended_action": "Inspect minidump crash files and run memory and system file diagnostics.",
                "action_type": "user_action",
                "user_steps": [
                    "1. Check C:\\Windows\\Minidump for recent .dmp crash dump files.",
                    "2. Run Windows Memory Diagnostic (mdsched.exe) to check for faulty RAM.",
                    "3. Run 'sfc /scannow' in Administrator PowerShell to verify system files.",
                    "4. Roll back any recently installed driver updates."
                ],
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True,
                "verification_plan": "Not applicable.",
                "fallback_action": "If Blue Screen crashes (BSOD) persist, test hardware components or perform clean Windows reinstallation."
            }

        elif cat == "printer":
            evidence = data.get("evidence", [])
            spooler_running = data.get("spooler_running", True)
            if not spooler_running:
                return {
                    "summary": "Print Spooler Service is stopped.",
                    "problem": "Windows Print Spooler service is stopped.",
                    "likely_causes": ["The Print Spooler service terminated or crashed due to a corrupted print job."],
                    "evidence": evidence,
                    "confidence": "HIGH",
                    "why": "Windows Service Manager reports Spooler status is not Running.",
                    "recommended_action": "Restart the Print Spooler service.",
                    "action_type": "automated_repair",
                    "user_steps": ["Click 'RUN REPAIR' below to restart the Print Spooler."],
                    "repair_id": "restart_spooler",
                    "repair_reason": "Restarts the Print Spooler service to resume print job processing.",
                    "risk": "low",
                    "cannot_fix": False,
                    "verification_plan": "FixIt AI will check Get-Service Spooler to confirm status is 'Running'.",
                    "fallback_action": "If Spooler stops again, delete stalled files in C:\\Windows\\System32\\spool\\PRINTERS."
                }
            else:
                return {
                    "summary": "Issue detected with installed printer.",
                    "problem": "Printer communication or status error.",
                    "likely_causes": ["Printer is offline, disconnected, or reported an error status."],
                    "evidence": evidence,
                    "confidence": "MEDIUM",
                    "why": "Printer query returned non-idle/error status code.",
                    "recommended_action": "Check printer connection and clear print queue.",
                    "action_type": "user_action",
                    "user_steps": [
                        "Check printer power, cable, and Wi-Fi connection.",
                        "Open Settings → Bluetooth & devices → Printers & scanners and clear print queue."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "Reinstall printer driver from manufacturer."
                }

        elif cat == "windows":
            evidence = data.get("evidence", [])
            wuauserv_running = data.get("wuauserv_running", True)
            if not wuauserv_running:
                return {
                    "summary": "Windows Update service is not running.",
                    "problem": "Windows Update service (wuauserv) is stopped.",
                    "likely_causes": ["The Windows Update service is stopped or disabled."],
                    "evidence": evidence,
                    "confidence": "HIGH",
                    "why": "Windows Service Manager reports wuauserv is not running.",
                    "recommended_action": "Restart the Windows Update service.",
                    "action_type": "automated_repair",
                    "user_steps": ["Click 'RUN REPAIR' below to restart Windows Update service."],
                    "repair_id": "restart_wuauserv",
                    "repair_reason": "Restarts the Windows Update service to fix stuck updates.",
                    "risk": "low",
                    "cannot_fix": False,
                    "verification_plan": "FixIt AI will verify Get-Service wuauserv reports status 'Running'.",
                    "fallback_action": "Run Windows Update Troubleshooter in Settings → System → Troubleshoot."
                }
            else:
                return {
                    "summary": "Windows reports recent system event errors.",
                    "problem": "System errors detected in Windows event log.",
                    "likely_causes": ["Windows logged recent errors in the System event log."],
                    "evidence": evidence,
                    "confidence": "MEDIUM",
                    "why": "Event log query returned error entries.",
                    "recommended_action": "Check Windows Event Viewer for specific error source details.",
                    "action_type": "user_action",
                    "user_steps": ["Open Event Viewer (eventvwr.msc) → Windows Logs → System."],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "Inspect logged error codes."
                }

        elif cat == "display":
            evidence = data.get("evidence", [])
            driver_error = (data.get("driver_status") == "error")
            if driver_error:
                return {
                    "summary": "Display adapter is reporting a driver or PnP error.",
                    "problem": "Display adapter (GPU) is reporting a PnP error.",
                    "likely_causes": ["Graphics driver crashed, encountered Code 43, or requires update."],
                    "evidence": evidence,
                    "confidence": "MEDIUM",
                    "why": "Windows PnP reports an error status for the primary display controller.",
                    "recommended_action": "Restart graphics driver via shortcut or reinstall latest GPU driver.",
                    "action_type": "user_action",
                    "user_steps": [
                        "1. Press Win + Ctrl + Shift + B to restart the Windows graphics driver.",
                        "2. Open Device Manager → Display adapters, right-click GPU, and check Properties.",
                        "3. Reinstall or update graphics drivers using manufacturer software (NVIDIA, AMD, Intel).",
                        "4. Restart your PC."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "If Code 43 persists after a clean driver install, hardware GPU diagnostic is recommended."
                }
            else:
                return {
                    "summary": "No display monitor detected by Windows PnP.",
                    "problem": "No display monitor detected by Windows PnP.",
                    "likely_causes": ["Monitor disconnected, display cable loose, or projection misconfigured."],
                    "evidence": evidence,
                    "confidence": "MEDIUM",
                    "why": "Windows PnP returned zero connected monitors.",
                    "recommended_action": "Check monitor connection and projection settings.",
                    "action_type": "user_action",
                    "user_steps": [
                        "Press Win + P to verify display projection mode.",
                        "Check video cable and monitor power."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "Test with an alternative display cable or external monitor."
                }

        elif cat == "keyboard":
            evidence = data.get("evidence", [])
            return {
                "summary": "Keyboard reporting PnP error or not detected.",
                "problem": "Keyboard device is reporting an error or is not detected.",
                "likely_causes": ["Keyboard driver communication failure, loose USB connection, or Filter Keys enabled."],
                "evidence": evidence,
                "confidence": "MEDIUM",
                "why": "Windows PnP reports an error or missing keyboard device node.",
                "recommended_action": "Uninstall keyboard device in Device Manager to force re-enumeration.",
                "action_type": "user_action",
                "user_steps": [
                    "1. Open Device Manager → Keyboards.",
                    "2. Right-click keyboard, select 'Uninstall device', then click 'Scan for hardware changes'.",
                    "3. In Windows Settings → Accessibility → Keyboard, ensure 'Filter Keys' is OFF.",
                    "4. For external keyboards, test a different USB port."
                ],
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True,
                "verification_plan": "Not applicable.",
                "fallback_action": "Test with an external USB keyboard to rule out physical laptop keyboard hardware failure."
            }

        elif cat in ["mouse", "mouse_touchpad", "input"]:
            evidence = data.get("evidence", [])
            return {
                "summary": "Pointing device reporting PnP error or not detected.",
                "problem": "Mouse or touchpad reporting an error or not detected.",
                "likely_causes": ["Touchpad toggled OFF via hotkey, driver error, or disconnected USB mouse."],
                "evidence": evidence,
                "confidence": "MEDIUM",
                "why": "Windows PnP reports an error or missing mouse/pointing device.",
                "recommended_action": "Check keyboard touchpad toggle key and Windows Touchpad settings.",
                "action_type": "user_action",
                "user_steps": [
                    "1. Check keyboard for touchpad toggle hotkey (Fn + F9 or Fn + F7).",
                    "2. In Windows Settings → Bluetooth & devices → Touchpad, verify Touchpad is ON.",
                    "3. Check Device Manager → Mice and other pointing devices.",
                    "4. For wireless mice, check batteries and USB receiver."
                ],
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True,
                "verification_plan": "Not applicable.",
                "fallback_action": "Test with a standard USB mouse to isolate physical touchpad hardware issues."
            }

        elif cat == "microphone":
            evidence = data.get("evidence", [])
            service_running = data.get("service_running", True)
            if not service_running:
                return {
                    "summary": "Windows Audio service is not running.",
                    "problem": "Windows Audio service is stopped (affects microphones).",
                    "likely_causes": ["AudioSrv service is stopped, disabling audio recording devices."],
                    "evidence": evidence,
                    "confidence": "HIGH",
                    "why": "Windows Service Manager reports AudioSrv is stopped.",
                    "recommended_action": "Restart the Windows Audio service.",
                    "action_type": "automated_repair",
                    "user_steps": ["Click 'RUN REPAIR' below to restart audio services."],
                    "repair_id": "restart_audio",
                    "repair_reason": "Restarting the Windows Audio service.",
                    "risk": "low",
                    "cannot_fix": False,
                    "verification_plan": "FixIt AI will check Get-Service AudioSrv to confirm status is 'Running'.",
                    "fallback_action": "Check microphone privacy settings if recording remains unavailable."
                }
            else:
                return {
                    "summary": "Microphone reporting issue.",
                    "problem": "Microphone recording device reporting an error or blocked by settings.",
                    "likely_causes": ["Microphone access disabled in Windows Privacy or device driver error."],
                    "evidence": evidence,
                    "confidence": "MEDIUM",
                    "why": "Windows PnP or service telemetry reports issue with recording device.",
                    "recommended_action": "Check Microphone privacy access and default input device.",
                    "action_type": "user_action",
                    "user_steps": [
                        "1. Open Windows Settings → Privacy & security → Microphone and ensure access is ON.",
                        "2. Check Sound Settings → Input to ensure the correct default microphone is selected.",
                        "3. Inspect Device Manager → Audio inputs and outputs."
                    ],
                    "repair_id": None,
                    "repair_reason": "",
                    "risk": "low",
                    "cannot_fix": True,
                    "verification_plan": "Not applicable.",
                    "fallback_action": "Test external headset microphone to verify if issue is isolated to onboard mic array."
                }

        elif cat == "usb":
            evidence = data.get("evidence", [])
            error_devs = data.get("error_devices", [])
            return {
                "summary": "USB controller or device error detected.",
                "problem": "USB controller or connected device is reporting a PnP error.",
                "likely_causes": ["USB device malfunction, power surge on hub, or driver initialization error."],
                "evidence": evidence,
                "confidence": "MEDIUM",
                "why": "Windows PnP reports Status Error on one or more USB controllers or endpoints.",
                "recommended_action": "Reconnect device to another port and reload USB controllers in Device Manager.",
                "action_type": "user_action",
                "user_steps": [
                    "1. Unplug the affected USB device and reconnect it to a different port.",
                    "2. Open Device Manager → Universal Serial Bus controllers.",
                    "3. Right-click the controller/hub with an error mark and select 'Uninstall device'.",
                    "4. Click Action → 'Scan for hardware changes' to reload the USB controller.",
                    "5. Under USB Root Hub Properties → Power Management, uncheck 'Allow computer to turn off this device'."
                ],
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True,
                "verification_plan": "Not applicable.",
                "fallback_action": "If all USB ports fail to recognize any device, motherboard chipset or USB controller hardware service is required."
            }

        elif cat == "battery":
            evidence = data.get("evidence", [])
            charge = data.get("charge_percent", 0)
            return {
                "summary": "Battery critically low and not charging.",
                "problem": f"Battery is critically low ({charge}%) and not charging.",
                "likely_causes": ["AC adapter disconnected, faulty charging cable, or worn battery pack."],
                "evidence": evidence,
                "confidence": "HIGH",
                "why": "Win32_Battery telemetry reports critical charge without active AC charging state.",
                "recommended_action": "Verify charger connection and generate battery health report.",
                "action_type": "user_action",
                "user_steps": [
                    "1. Verify charger is firmly connected to the laptop and a working wall socket.",
                    "2. Check the charging LED indicator on the laptop chassis.",
                    "3. Run 'powercfg /batteryreport' in PowerShell to inspect battery degradation.",
                    "4. If laptop powers off instantly when disconnected from AC, battery replacement is required."
                ],
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True,
                "verification_plan": "Not applicable.",
                "fallback_action": "If the charger is verified working on another device but this laptop will not charge, hardware inspection of the DC-in jack or motherboard charging circuit is justified."
            }

        elif cat == "storage":
            evidence = data.get("evidence", [])
            return {
                "summary": "Critically low disk space detected.",
                "problem": "Drive partition is critically low on free disk space (< 5% free).",
                "likely_causes": ["Drive is filled with temporary files, system restore points, or large downloads."],
                "evidence": evidence,
                "confidence": "HIGH",
                "why": "Windows Volume telemetry reports drive free capacity below 5%.",
                "recommended_action": "Run Disk Cleanup and clear temporary files.",
                "action_type": "user_action",
                "user_steps": [
                    "1. Press Win + R, type cleanmgr, and run Disk Cleanup.",
                    "2. Empty the Recycle Bin.",
                    "3. Open Settings → System → Storage and enable Storage Sense.",
                    "4. Move large files or uninstall unused apps."
                ],
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True,
                "verification_plan": "Not applicable.",
                "fallback_action": "Use an external drive or upgrade SSD capacity if storage remains constrained."
            }

        elif cat == "performance":
            evidence = data.get("evidence", [])
            cpu_load = data.get("cpu_load", 0)
            mem_load = data.get("mem_load", 0)
            return {
                "summary": "High system resource load detected.",
                "problem": f"System experiencing sustained high resource load (CPU: {cpu_load}%, RAM: {mem_load:.0f}%).",
                "likely_causes": ["Background processes consuming excessive CPU cycles or memory leak."],
                "evidence": evidence,
                "confidence": "HIGH",
                "why": "Performance telemetry exceeds high sustained threshold (> 95%).",
                "recommended_action": "Open Task Manager to identify and terminate demanding processes.",
                "action_type": "user_action",
                "user_steps": [
                    "1. Press Ctrl + Shift + Esc to open Task Manager.",
                    "2. Sort by CPU and Memory to locate demanding processes.",
                    "3. Close heavy browser tabs or background applications.",
                    "4. Restart the PC to clear memory leaks."
                ],
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True,
                "verification_plan": "Not applicable.",
                "fallback_action": "Check for malware or run clean boot troubleshooting if resource consumption persists after restarting."
            }

        elif cat == "drivers":
            evidence = data.get("evidence", [])
            err_cnt = data.get("error_count", len(evidence))
            return {
                "summary": f"Detected {err_cnt} devices with driver errors.",
                "problem": f"Windows reports {err_cnt} device(s) with PnP or driver errors.",
                "likely_causes": ["Missing, outdated, or corrupted device drivers reporting PnP error codes."],
                "evidence": evidence,
                "confidence": "HIGH",
                "why": "Windows PnP returned devices in Error status.",
                "recommended_action": "Install pending Windows driver updates and inspect Device Manager.",
                "action_type": "user_action",
                "user_steps": [
                    "1. Open Windows Update and install all pending quality and optional driver updates.",
                    "2. Open Device Manager (devmgmt.msc) and locate devices marked with a yellow exclamation point.",
                    "3. Right-click each device and check Properties for the specific PnP error code (e.g. Code 10, Code 28, Code 43).",
                    "4. Download driver packages from the computer manufacturer support site."
                ],
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True,
                "verification_plan": "Not applicable.",
                "fallback_action": "If drivers fail to install, boot into Safe Mode to remove conflicting legacy drivers."
            }

        # Generic subsystem problem fallback
        evidence = data.get("evidence", [f"Issue detected with {cat}."])
        return {
            "summary": f"Issue detected with {cat}.",
            "problem": f"Issue detected with {cat} subsystem.",
            "likely_causes": ["System telemetry reports an issue with this subsystem."],
            "evidence": evidence,
            "confidence": "MEDIUM",
            "why": "Telemetry returned problem status for this subsystem.",
            "recommended_action": "Open Device Manager and Windows Event Viewer for detailed logs.",
            "action_type": "user_action",
            "user_steps": [
                "Open Windows Device Manager.",
                "Inspect the subsystem for error codes.",
                "Restart the PC."
            ],
            "repair_id": None,
            "repair_reason": "",
            "risk": "low",
            "cannot_fix": True,
            "verification_plan": "Not applicable.",
            "fallback_action": "Check manufacturer support documentation."
        }


class OllamaBackend(InferenceBackend):
    def __init__(self, ollama_url=None, model_name=None, enabled=None):
        if enabled is not None:
            self.enabled = bool(enabled)
        else:
            val = os.getenv("USE_LOCAL_LLM")
            if val is not None:
                self.enabled = val.strip().lower() in ("true", "1", "yes")
            else:
                self.enabled = True
                
        self.ollama_url = (ollama_url or os.getenv("OLLAMA_URL") or "http://localhost:11434").rstrip("/")
        self.model_name = model_name or os.getenv("LLM_MODEL") or os.getenv("OLLAMA_MODEL") or "llama2"
        self.available = self._check_availability() if self.enabled else False
        
        self.system_prompt = """You are FixIt AI, an offline Windows troubleshooting technician.
Rules:
- Ground your analysis strictly in the provided Windows telemetry evidence.
- Do NOT claim certainty without evidence. Use HIGH, MEDIUM, or LOW confidence based on facts.
- Do NOT claim 'corrupted driver', 'hardware failure', or 'malware' unless evidence explicitly confirms it.
- Distinguish between:
  1. Safe automated repairs from the catalog
  2. Additional user actions (Device Manager, settings, reboots)
  3. Hardware escalation (only when telemetry indicates hardware failure or software steps exhausted)
- NEVER generate executable commands. Select ONLY repair IDs from the valid catalog.
- If status is 'unavailable', summary must be 'Diagnostic Unavailable.' and cannot_fix=true.
- If status is 'unknown', summary must be 'Windows diagnostic command failed.' and cannot_fix=true.
- You MUST reply with strictly valid JSON matching this schema:

{
    "summary": "1-2 sentence overview",
    "problem": "Short specific problem description",
    "likely_causes": ["cause 1", "cause 2"],
    "evidence": ["evidence 1", "evidence 2"],
    "confidence": "HIGH|MEDIUM|LOW",
    "why": "Short explanation connecting evidence to conclusion",
    "recommended_action": "Specific next action",
    "action_type": "automated_repair|user_action|escalation|none",
    "user_steps": ["step 1", "step 2"],
    "repair_id": "string ID from catalog or null",
    "repair_reason": "why this repair will help",
    "risk": "low|medium|high",
    "cannot_fix": false,
    "verification_plan": "what will be checked after repair",
    "fallback_action": "next diagnostic or user step if fix fails"
}

VALID REPAIR CATALOG (use ONLY these for repair_id):
- "enable_wifi"
- "restart_wlan"
- "ip_renew"
- "flush_dns"
- "restart_audio"
- "restart_bluetooth"
- "enable_camera"
- "restart_spooler"
- "restart_wuauserv"
"""

    def _check_availability(self):
        if not getattr(self, 'enabled', True):
            return False
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    models = [m.get("name", "") for m in data.get("models", [])]
                    target = self.model_name.lower().strip()
                    target_base = target.split(":")[0]
                    for m in models:
                        m_lower = m.lower().strip()
                        base = m_lower.split(":")[0]
                        if target == m_lower or target == base or target_base == base or target in m_lower or base in target:
                            return True
            return False
        except Exception:
            return False

    def _call_ollama(self, prompt, is_retry=False):
        sys_prompt = self.system_prompt
        if is_retry:
            sys_prompt += "\n\nCRITICAL: Your previous response was invalid JSON. You MUST return strictly parseable JSON."
            
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": f"Diagnostic Data:\n{json.dumps(prompt, indent=2)}"}
            ],
            "stream": False,
            "format": "json"
        }
        
        req = urllib.request.Request(f"{self.ollama_url}/api/chat", 
                                     data=json.dumps(payload).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    resp_data = json.loads(response.read().decode('utf-8'))
                    return resp_data.get("message", {}).get("content", "")
        except Exception:
            return None
        return None

    def generate(self, data):
        if not self.available:
            return None
            
        for attempt in range(2):
            result_str = self._call_ollama(data, is_retry=(attempt > 0))
            if not result_str:
                break
            try:
                cleaned_str = result_str.strip()
                if "```" in cleaned_str:
                    import re
                    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned_str)
                    if match:
                        cleaned_str = match.group(1).strip()
                start = cleaned_str.find("{")
                end = cleaned_str.rfind("}")
                if start != -1 and end != -1 and end > start:
                    cleaned_str = cleaned_str[start:end+1]
                    
                parsed = json.loads(cleaned_str)
                
                if isinstance(parsed, dict) and "summary" in parsed and "cannot_fix" in parsed:
                    valid = [
                        "enable_wifi", "restart_wlan", "ip_renew", "flush_dns",
                        "restart_audio", "restart_bluetooth", "enable_camera",
                        "restart_spooler", "restart_wuauserv", None
                    ]
                    if parsed.get("repair_id") not in valid:
                        parsed["repair_id"] = None
                    return parsed
            except (json.JSONDecodeError, Exception):
                continue
        return None

class ONNXBackend(InferenceBackend):
    def __init__(self):
        self.available = False
        self.model_name = "Not Loaded"
        
    def generate(self, data):
        return None

class QNNBackend(InferenceBackend):
    def __init__(self):
        self.available = False
        self.model_name = "Not Loaded"
        
    def generate(self, data):
        return None

class LocalAIEngine:
    def __init__(self, use_local_llm=None):
        if use_local_llm is not None:
            self.use_local_llm = bool(use_local_llm)
        else:
            val = os.getenv("USE_LOCAL_LLM", "false").strip().lower()
            self.use_local_llm = val in ("true", "1", "yes")

        self.backends = {
            "qnn": QNNBackend(),
            "onnx": ONNXBackend(),
            "llm": OllamaBackend(enabled=self.use_local_llm),
            "rule": RuleBasedBackend()
        }
        
    def get_active_backend_info(self):
        for name in ["qnn", "onnx", "llm"]:
            backend = self.backends[name]
            if getattr(backend, 'available', False):
                return {
                    "backend": name.upper(), 
                    "model": getattr(backend, 'model_name', 'Unknown')
                }
        return {"backend": "RULE-BASED", "model": "Deterministic"}

    def is_available(self):
        return True 

    def explain_diagnosis(self, diagnosis_data):
        res = None
        for name in ["qnn", "onnx", "llm"]:
            backend = self.backends[name]
            if getattr(backend, 'available', False):
                try:
                    res = backend.generate(diagnosis_data)
                except Exception:
                    res = None
                if not res:
                    # Backend generated invalid output or timed out; recheck availability
                    if hasattr(backend, '_check_availability'):
                        backend.available = backend._check_availability()
                else:
                    break
        if not res:
            res = self.backends["rule"].generate(diagnosis_data)


        # Normalize and ensure all structured technician fields are present
        if res:
            summary = res.get("summary", "Issue detected.")
            if "problem" not in res or not res["problem"]:
                res["problem"] = summary
            if "likely_causes" not in res:
                res["likely_causes"] = []
            if "evidence" not in res:
                res["evidence"] = diagnosis_data.get("evidence", [])
            if "confidence" not in res:
                res["confidence"] = "MEDIUM"
            else:
                res["confidence"] = str(res["confidence"]).upper()
            if "why" not in res or not res["why"]:
                res["why"] = "Windows telemetry indicates an issue with this subsystem."
            if "repair_id" not in res:
                res["repair_id"] = None
            if "repair_reason" not in res:
                res["repair_reason"] = ""
            if "risk" not in res:
                res["risk"] = "low"
            if "cannot_fix" not in res:
                res["cannot_fix"] = (res.get("repair_id") is None and diagnosis_data.get("status") != "healthy")
            
            # Action type normalization
            if "action_type" not in res or not res["action_type"]:
                if res.get("repair_id"):
                    res["action_type"] = "automated_repair"
                elif res.get("cannot_fix"):
                    res["action_type"] = "user_action"
                else:
                    res["action_type"] = "none"

            if "recommended_action" not in res or not res["recommended_action"]:
                if res["action_type"] == "automated_repair":
                    res["recommended_action"] = f"Run safe repair: {res.get('repair_id')}"
                elif res["action_type"] == "user_action":
                    res["recommended_action"] = "Inspect device in Windows Device Manager and restart PC."
                else:
                    res["recommended_action"] = "No action needed."

            if "user_steps" not in res:
                res["user_steps"] = []
            if "verification_plan" not in res or not res["verification_plan"]:
                if res.get("repair_id"):
                    res["verification_plan"] = f"FixIt AI will verify subsystem state following {res['repair_id']}."
                else:
                    res["verification_plan"] = "Not applicable."
            if "fallback_action" not in res or not res["fallback_action"]:
                res["fallback_action"] = "If issue persists, consult device documentation or contact manufacturer support."

        return res
