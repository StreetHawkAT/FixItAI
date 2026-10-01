import pytest
from core.ai_engine import LocalAIEngine

@pytest.fixture
def engine():
    return LocalAIEngine()

# ==================== CAMERA TESTS ====================

def test_camera_healthy(engine):
    data = {
        "category": "camera",
        "status": "healthy",
        "camera_present": True,
        "camera_enabled": True,
        "devices": [{"Name": "Integrated Camera", "Status": "OK", "Problem": 0}],
        "evidence": ["Detected 1 camera/imaging device(s).", "Device: Integrated Camera | Status: OK | PnP Code: 0"]
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] is None
    assert res["cannot_fix"] == False
    assert res["action_type"] == "none"
    assert res["confidence"] == "HIGH"
    assert "normally" in res["summary"].lower() or "healthy" in res["problem"].lower()

def test_camera_disabled(engine):
    data = {
        "category": "camera",
        "status": "problem",
        "camera_present": True,
        "camera_enabled": False,
        "device_status": "disabled",
        "disabled_cameras": ["Integrated Camera"],
        "devices": [{"Name": "Integrated Camera", "Status": "Error", "Problem": 22, "ProblemDescription": "This device is disabled. (Code 22)."}],
        "evidence": ["Device: Integrated Camera | Status: Error | PnP Code: 22 (This device is disabled. (Code 22).)"]
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] == "enable_camera"
    assert res["action_type"] == "automated_repair"
    assert res["cannot_fix"] == False
    assert res["confidence"] == "HIGH"
    assert "disabled" in res["problem"].lower() or "disabled" in res["summary"].lower()
    assert "verification_plan" in res
    assert "fallback_action" in res

def test_camera_generic_error(engine):
    data = {
        "category": "camera",
        "status": "problem",
        "camera_present": True,
        "camera_enabled": False,
        "driver_status": "error",
        "device_status": "error",
        "devices": [{"Name": "HD Webcam", "Status": "Error"}],
        "evidence": ["Device: HD Webcam | Status: Error"]
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] is None
    assert res["cannot_fix"] == True
    assert res["action_type"] == "user_action"
    assert res["confidence"] in ["LOW", "MEDIUM"]
    # Ensure it does NOT make an unsubstantiated corrupted driver claim
    assert "corrupted" not in res["why"].lower()
    assert len(res["user_steps"]) > 0

def test_camera_specific_pnp_error_code(engine):
    data = {
        "category": "camera",
        "status": "problem",
        "camera_present": True,
        "camera_enabled": False,
        "driver_status": "error",
        "device_status": "error",
        "devices": [{"Name": "HD Webcam", "Status": "Error", "Problem": 10, "ProblemDescription": "This device cannot start. (Code 10)."}],
        "evidence": ["Device: HD Webcam | Status: Error | PnP Code: 10 (This device cannot start. (Code 10).)"]
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] is None
    assert res["cannot_fix"] == True
    assert res["action_type"] == "user_action"
    assert res["confidence"] == "MEDIUM"
    assert "10" in res["why"] or "10" in str(res["evidence"])
    assert "corrupted" not in res["why"].lower()

def test_camera_one_healthy_one_unhealthy(engine):
    data = {
        "category": "camera",
        "status": "problem",
        "camera_present": True,
        "camera_enabled": True,
        "driver_status": "error",
        "total_cameras": 2,
        "healthy_cameras": ["ASUS IR camera"],
        "problem_cameras": ["ASUS FHD webcam"],
        "devices": [
            {"Name": "ASUS IR camera", "Status": "OK", "Problem": 0},
            {"Name": "ASUS FHD webcam", "Status": "Error", "Problem": 10}
        ],
        "evidence": [
            "Detected 2 camera/imaging device(s).",
            "Device: ASUS IR camera | Status: OK | PnP Code: 0",
            "Device: ASUS FHD webcam | Status: Error | PnP Code: 10",
            "Windows Camera Frame Server service: Running"
        ]
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] is None
    assert res["cannot_fix"] == True
    assert res["action_type"] == "user_action"
    assert res["confidence"] == "MEDIUM"
    assert "ASUS IR camera" in res["problem"]
    assert "ASUS FHD webcam" in res["problem"]
    assert "corrupted" not in res["why"].lower()
    # It must note that the other camera is healthy
    assert "ASUS IR camera" in res["why"] or "healthy" in res["why"]

def test_camera_none_detected(engine):
    data = {
        "category": "camera",
        "status": "problem",
        "camera_present": False,
        "total_cameras": 0,
        "devices": [],
        "evidence": ["0 camera/imaging devices enumerated in Windows PnP."]
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] is None
    assert res["cannot_fix"] == True
    assert res["action_type"] == "user_action"
    assert "shutter" in str(res["likely_causes"]).lower() or "shutter" in str(res["user_steps"]).lower()

def test_camera_privacy_denied(engine):
    data = {
        "category": "camera",
        "status": "problem",
        "camera_present": True,
        "privacy_access": "deny",
        "devices": [{"Name": "Integrated Camera", "Status": "OK"}],
        "evidence": ["Windows Camera Privacy setting: Deny"]
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] is None
    assert res["cannot_fix"] == True
    assert res["action_type"] == "user_action"
    assert res["confidence"] == "HIGH"
    assert "privacy" in res["problem"].lower() or "privacy" in res["why"].lower()

def test_camera_insufficient_evidence(engine):
    data = {
        "category": "camera",
        "status": "problem"
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] is None
    assert res["cannot_fix"] == True
    assert res["confidence"] == "LOW"

# ==================== NETWORK TESTS ====================

def test_network_healthy(engine):
    data = {
        "category": "network",
        "status": "healthy",
        "internet_connected": True,
        "wifi_present": True,
        "wifi_enabled": True
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] is None
    assert res["cannot_fix"] == False
    assert res["action_type"] == "none"

def test_network_disconnected_disabled_adapter(engine):
    data = {
        "category": "network",
        "status": "problem",
        "internet_connected": False,
        "wifi_present": True,
        "wifi_enabled": False,
        "wlan_service": "running"
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] == "enable_wifi"
    assert res["action_type"] == "automated_repair"
    assert res["confidence"] == "HIGH"

def test_network_dhcp_issue(engine):
    data = {
        "category": "network",
        "status": "problem",
        "internet_connected": False,
        "wifi_present": True,
        "wifi_enabled": True,
        "dhcp_failed": True
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] == "ip_renew"
    assert res["action_type"] == "automated_repair"

def test_network_wlan_stopped(engine):
    data = {
        "category": "network",
        "status": "problem",
        "internet_connected": False,
        "wifi_present": False,
        "wlan_service": "stopped"
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] == "restart_wlan"
    assert res["confidence"] == "HIGH"

# ==================== AUDIO TESTS ====================

def test_audio_healthy(engine):
    data = {
        "category": "audio",
        "status": "healthy",
        "service_running": True
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] is None
    assert res["cannot_fix"] == False

def test_audio_service_stopped(engine):
    data = {
        "category": "audio",
        "status": "problem",
        "service_running": False
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] == "restart_audio"
    assert res["action_type"] == "automated_repair"
    assert res["confidence"] == "HIGH"

def test_audio_device_error(engine):
    data = {
        "category": "audio",
        "status": "problem",
        "service_running": True,
        "driver_status": "error"
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] is None
    assert res["cannot_fix"] == True
    assert res["action_type"] == "user_action"
    assert res["confidence"] == "MEDIUM"

# ==================== BLUETOOTH TESTS ====================

def test_bluetooth_service_stopped(engine):
    data = {
        "category": "bluetooth",
        "status": "problem",
        "service_running": False,
        "driver_status": "ok"
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] == "restart_bluetooth"
    assert res["confidence"] == "HIGH"

def test_bluetooth_device_error(engine):
    data = {
        "category": "bluetooth",
        "status": "problem",
        "service_running": True,
        "driver_status": "error"
    }
    res = engine.explain_diagnosis(data)
    assert res["repair_id"] is None
    assert res["cannot_fix"] == True
    assert res["action_type"] == "user_action"
    assert "corrupted" not in res["why"].lower()
