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

def check_camera():
    ps_cmd = """
    $pnp = @(Get-PnpDevice -Class Camera, Image -ErrorAction SilentlyContinue | Select-Object Name, Status, Present, Class, InstanceId, Problem, ProblemDescription);
    $svc = (Get-Service -Name FrameServer -ErrorAction SilentlyContinue).Status.ToString();
    $priv = (Get-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\webcam' -Name Value -ErrorAction SilentlyContinue).Value;
    [PSCustomObject]@{ Devices = $pnp; FrameServer = $svc; Privacy = $priv } | ConvertTo-Json -Compress -Depth 3
    """
    raw_output = run_ps(ps_cmd)
    devices = []
    frame_server = "Not available"
    privacy_setting = "Not available"

    if raw_output:
        try:
            parsed = json.loads(raw_output)
            if isinstance(parsed, dict) and "Devices" in parsed:
                dev_data = parsed.get("Devices")
                if isinstance(dev_data, list):
                    devices = dev_data
                elif isinstance(dev_data, dict):
                    devices = [dev_data]
                frame_server = parsed.get("FrameServer") or "Not available"
                privacy_setting = parsed.get("Privacy") or "Not available"
            elif isinstance(parsed, list):
                devices = parsed
            elif isinstance(parsed, dict):
                devices = [parsed]
        except Exception:
            pass

    camera_present = len(devices) > 0
    camera_enabled = False
    driver_error = False
    device_status = "not_detected"

    healthy_cameras = []
    disabled_cameras = []
    error_cameras = []
    problem_cameras = []

    evidence = []

    if camera_present:
        evidence.append(f"Detected {len(devices)} camera/imaging device(s).")

        for d in devices:
            name = d.get("Name") or d.get("FriendlyName") or "Unknown Camera"
            status = str(d.get("Status", "UNKNOWN")).upper()
            prob = d.get("Problem")
            prob_desc = d.get("ProblemDescription") or "Not available"

            is_dev_disabled = (prob == 22 or "disabled" in str(prob_desc).lower() or status == "DISABLED")

            if status == "OK" and (prob == 0 or prob is None):
                healthy_cameras.append(name)
                camera_enabled = True
            else:
                problem_cameras.append(d)
                if is_dev_disabled:
                    disabled_cameras.append(d)
                else:
                    error_cameras.append(d)
                    driver_error = True

            if prob is not None and prob_desc != "Not available":
                evidence.append(f"Device: {name} | Status: {status} | PnP Code: {prob} ({prob_desc})")
            elif prob is not None:
                evidence.append(f"Device: {name} | Status: {status} | PnP Code: {prob}")
            else:
                evidence.append(f"Device: {name} | Status: {status}")

        if frame_server and frame_server != "Not available":
            evidence.append(f"Windows Camera Frame Server service: {frame_server}")
        if privacy_setting and privacy_setting != "Not available":
            evidence.append(f"Windows Camera Privacy setting: {privacy_setting}")

        if len(healthy_cameras) == len(devices):
            device_status = "ok"
        elif disabled_cameras and not error_cameras and not healthy_cameras:
            device_status = "disabled"
        elif error_cameras:
            device_status = "error"
        elif healthy_cameras and (disabled_cameras or error_cameras):
            device_status = "partial_error"
        else:
            device_status = "unknown"
    else:
        evidence.append("No camera device was detected by Windows.")

    status = "healthy"
    if not camera_present:
        status = "problem"
    elif problem_cameras:
        status = "problem"
    elif frame_server.lower() == "stopped":
        status = "problem"
    elif privacy_setting.lower() == "deny":
        status = "problem"

    return {
        "category": "camera",
        "status": status,
        "camera_present": camera_present,
        "camera_enabled": camera_enabled,
        "driver_status": "error" if driver_error else "ok",
        "device_status": device_status,
        "devices": devices,
        "total_cameras": len(devices),
        "healthy_cameras": healthy_cameras,
        "disabled_cameras": [d.get("Name", "Camera") for d in disabled_cameras],
        "problem_cameras": [d.get("Name", "Camera") for d in problem_cameras],
        "frame_server_service": frame_server,
        "privacy_access": privacy_setting,
        "evidence": evidence
    }

