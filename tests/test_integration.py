import pytest
from core.ai_engine import LocalAIEngine
from core.repair_engine import RepairEngine
from diagnostics.audio import check_audio

def test_ai_fallback_unknown():
    engine = LocalAIEngine()
    data = {"category": "display", "status": "unknown"}
    # Force rule-based fallback
    result = engine.backends["rule"].generate(data)
    assert result["summary"] == "Windows diagnostic command failed."
    assert result["cannot_fix"] == True

def test_ai_fallback_unavailable():
    engine = LocalAIEngine()
    data = {"category": "printer", "status": "unavailable"}
    result = engine.backends["rule"].generate(data)
    assert result["summary"] == "Diagnostic Unavailable."
    assert result["cannot_fix"] == True

def test_ai_fallback_healthy():
    engine = LocalAIEngine()
    data = {"category": "keyboard", "status": "healthy", "evidence": ["Keyboard OK"]}
    result = engine.backends["rule"].generate(data)
    assert result["summary"] == "System functioning normally."
    assert result["cannot_fix"] == False

def test_ai_schema_validation():
    engine = LocalAIEngine()
    data = {"category": "network", "status": "problem", "internet_connected": False, "wifi_present": False, "ethernet_present": False}
    result = engine.explain_diagnosis(data)
    # Validate core schema fields are present
    assert "summary" in result
    assert "likely_causes" in result
    assert "evidence" in result
    assert "cannot_fix" in result

def test_repair_engine_catalog():
    engine = RepairEngine()
    repairs = engine.get_available_repairs()
    # Check that all allowlisted LLM repairs exist in the actual execution engine
    allowlist = ["enable_wifi", "restart_wlan", "ip_renew", "flush_dns", "restart_audio", "restart_bluetooth", "enable_camera", "restart_spooler", "restart_wuauserv"]
    for r in allowlist:
        assert r in repairs, f"Repair {r} missing from execution engine!"
        
    for r_id, r_info in repairs.items():
        assert "execute" in r_info
        assert "verify" in r_info
        assert "risk" in r_info
