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
        
        engine = LocalAIEngine()
        result = engine.explain_diagnosis({
            "category": "network",
            "status": "problem",
            "internet_connected": False,
            "wifi_present": True,
            "wifi_enabled": False
        })
        assert result is not None
        assert result["repair_id"] == "enable_wifi"
