import pytest
import json
from unittest.mock import patch, MagicMock
from core.ai_engine import OllamaBackend, LocalAIEngine

def test_ollama_unavailable():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = Exception("Connection refused")
        backend = OllamaBackend()
        assert backend.available == False

def test_ollama_available_but_model_missing():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({"models": [{"name": "llama2:latest"}]}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        
        backend = OllamaBackend(model_name="phi3")
        assert backend.available == False

def test_valid_json_response():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp1 = MagicMock()
        mock_resp1.status = 200
        mock_resp1.read.return_value = json.dumps({"models": [{"name": "phi3:latest"}]}).encode('utf-8')
        
        mock_resp2 = MagicMock()
        mock_resp2.status = 200
        fake_llm_json = {
            "summary": "test summary",
            "likely_causes": [],
            "evidence": [],
            "confidence": "high",
            "repair_id": "enable_wifi",
            "repair_reason": "why",
            "risk": "low",
            "cannot_fix": False
        }
        mock_resp2.read.return_value = json.dumps({"message": {"content": json.dumps(fake_llm_json)}}).encode('utf-8')
        
        mock_urlopen.return_value.__enter__.side_effect = [mock_resp1, mock_resp2]
        
        backend = OllamaBackend(model_name="phi3")
        assert backend.available == True
        
        result = backend.generate({"category": "network"})
        assert result is not None
        assert result["repair_id"] == "enable_wifi"

def test_invalid_json_fallback():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp1 = MagicMock()
        mock_resp1.status = 200
        mock_resp1.read.return_value = json.dumps({"models": [{"name": "phi3:latest"}]}).encode('utf-8')
        
        mock_resp2 = MagicMock()
        mock_resp2.status = 200
        mock_resp2.read.return_value = json.dumps({"message": {"content": "This is just prose, no JSON."}}).encode('utf-8')
        
        mock_urlopen.return_value.__enter__.side_effect = [mock_resp1, mock_resp2, mock_resp2]
        
        backend = OllamaBackend(model_name="phi3")
        result = backend.generate({"category": "network"})
        assert result is None

def test_ai_engine_fallback():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp1 = MagicMock()
        mock_resp1.status = 200
        mock_resp1.read.return_value = json.dumps({"models": [{"name": "phi3:latest"}]}).encode('utf-8')
        
        mock_resp2 = MagicMock()
        mock_resp2.status = 200
        mock_resp2.read.return_value = json.dumps({"message": {"content": "Bad JSON"}}).encode('utf-8')
        
        mock_urlopen.return_value.__enter__.side_effect = [mock_resp1, mock_resp2, mock_resp2]
        
        engine = LocalAIEngine(use_local_llm=True)
        result = engine.explain_diagnosis({
            "category": "network",
            "status": "problem",
            "internet_connected": False,
            "wifi_present": True,
            "wifi_enabled": False
        })
        assert result is not None
        assert result["repair_id"] == "enable_wifi"

def test_use_local_llm_false_returns_rule_based():
    """Verify that USE_LOCAL_LLM=false forces Rule-Based backend and reports RULE-BASED in UI."""
    engine = LocalAIEngine(use_local_llm=False)
    info = engine.get_active_backend_info()
    assert info["backend"] == "RULE-BASED"
    assert info["model"] == "Deterministic"
    
    result = engine.explain_diagnosis({
        "category": "network",
        "status": "problem",
        "internet_connected": False,
        "wifi_present": True,
        "wifi_enabled": False
    })
    assert result["repair_id"] == "enable_wifi"
    assert result["action_type"] == "automated_repair"

def test_ollama_unavailable_never_claims_llm():
    """Verify UI does NOT claim LLM is active when Ollama is unreachable even if USE_LOCAL_LLM=true."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = Exception("Connection refused to port 11434")
        
        engine = LocalAIEngine(use_local_llm=True)
        info = engine.get_active_backend_info()
        assert info["backend"] == "RULE-BASED"
        assert info["backend"] != "LLM"

def test_ollama_timeout_fallback_to_rule_based():
    """Verify that when Ollama times out during inference, engine falls back to Rule-Based gracefully."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp1 = MagicMock()
        mock_resp1.status = 200
        mock_resp1.read.return_value = json.dumps({"models": [{"name": "llama2:latest"}]}).encode('utf-8')
        
        # Second call (chat inference) raises TimeoutError
        mock_urlopen.return_value.__enter__.side_effect = [mock_resp1, TimeoutError("Inference timed out")]
        
        engine = LocalAIEngine(use_local_llm=True)
        result = engine.explain_diagnosis({
            "category": "camera",
            "status": "problem",
            "camera_present": True,
            "camera_enabled": False,
            "device_status": "disabled",
            "disabled_cameras": ["ASUS FHD webcam"],
            "devices": [{"Name": "ASUS FHD webcam", "Status": "Error", "Problem": 22}],
            "evidence": ["Device: ASUS FHD webcam | PnP Code: 22"]
        })
        assert result is not None
        assert result["repair_id"] == "enable_camera"
        assert result["action_type"] == "automated_repair"
        assert result["confidence"] == "HIGH"

def test_ollama_arbitrary_repair_rejected_by_safety_boundary():
    """Verify that if LLM hallucinates an arbitrary PowerShell command or unallowlisted repair ID, it is sanitized to None."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp1 = MagicMock()
        mock_resp1.status = 200
        mock_resp1.read.return_value = json.dumps({"models": [{"name": "phi3:latest"}]}).encode('utf-8')
        
        mock_resp2 = MagicMock()
        mock_resp2.status = 200
        dangerous_llm_json = {
            "summary": "Fixing system",
            "likely_causes": ["Glitch"],
            "evidence": [],
            "confidence": "HIGH",
            "repair_id": "rmdir /s /q C:\\Windows",
            "repair_reason": "dangerous action",
            "risk": "high",
            "cannot_fix": False
        }
        mock_resp2.read.return_value = json.dumps({"message": {"content": json.dumps(dangerous_llm_json)}}).encode('utf-8')
        mock_urlopen.return_value.__enter__.side_effect = [mock_resp1, mock_resp2]
        
        backend = OllamaBackend(model_name="phi3", enabled=True)
        res = backend.generate({"category": "network"})
        assert res is not None
        # Must be sanitized to None because it is not in the allowlist!
        assert res["repair_id"] is None

