import pytest
from core.ai_engine import LocalAIEngine

def test_rule_based_network_offline():
    engine = LocalAIEngine()
    
    data = {
        "category": "network",
        "status": "problem",
        "internet_connected": False,
        "wifi_present": True,
        "wifi_enabled": False,
        "wlan_service": "running"
    }
    
    result = engine.explain_diagnosis(data)
    assert result["summary"] == "Internet connection unavailable."
    assert result["repair_id"] == "enable_wifi"
    assert "Wi-Fi adapter detected" in result["evidence"]
    assert "Adapter disabled" in result["evidence"]

def test_rule_based_crash():
    engine = LocalAIEngine()
    
    data = {
        "category": "crash",
        "status": "problem",
        "recent_crashes": [{"Id": 41, "ProviderName": "Kernel-Power"}]
    }
    
    result = engine.explain_diagnosis(data)
    assert "Detected 1 recent system crashes." in result["summary"]
    assert result.get("cannot_fix") == True
