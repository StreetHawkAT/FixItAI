import json
import urllib.request
import os

class InferenceBackend:
    def generate(self, data):
        raise NotImplementedError

class RuleBasedBackend(InferenceBackend):
    def generate(self, data):
        status = data.get("status", "unknown")
        cat = data.get("category", "")
        
        if status == "unavailable":
            return {
                "summary": "Diagnostic Unavailable.",
                "likely_causes": ["Diagnostic module not yet implemented for this category."],
                "evidence": ["Module unavailable"],
                "confidence": "high",
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True
            }
            
        if status == "unknown":
            return {
                "summary": "Windows diagnostic command failed.",
                "likely_causes": ["PowerShell/WMI execution failed or returned invalid data."],
                "evidence": data.get("evidence", ["Diagnostic execution failure."]),
                "confidence": "high",
                "repair_id": None,
                "repair_reason": "",
                "risk": "low",
                "cannot_fix": True
            }

        diagnosis = {
            "summary": "System functioning normally." if status == "healthy" else f"Problem detected in {cat} subsystem.",
            "likely_causes": [],
            "evidence": data.get("evidence", []),
            "confidence": "high",
            "repair_id": None,
            "repair_reason": "",
            "risk": "low",
            "cannot_fix": False
        }

        if cat == "network":
            if not data.get("internet_connected"):
                diagnosis["summary"] = "Internet connection unavailable."
                
                # Make sure we construct evidence if it's empty
                evidence = data.get("evidence", [])
                if not evidence:
                    if data.get("wifi_present"): evidence.append("Wi-Fi adapter detected")
                    else: evidence.append("Wi-Fi adapter not found")
                    
                    if data.get("wifi_enabled"): evidence.append("Adapter enabled")
                    elif data.get("wifi_present"): evidence.append("Adapter disabled")
                    
                    if data.get("wlan_service", "").lower() == "running":
                        evidence.append("WLAN service running")
                    else:
                        evidence.append("WLAN service stopped")
                diagnosis["evidence"] = evidence
                
                if not data.get("wifi_present") and not data.get("ethernet_present"):
                    diagnosis["likely_causes"] = ["No network adapters are present."]
                    diagnosis["cannot_fix"] = True
                elif data.get("driver_status") == "error":
                    diagnosis["likely_causes"] = ["Network driver is reporting an error."]
                    diagnosis["cannot_fix"] = True
                elif data.get("wifi_present") and not data.get("wifi_enabled"):
                    diagnosis["likely_causes"] = ["The Wi-Fi adapter is present but disabled."]
                    diagnosis["repair_id"] = "enable_wifi"
                    diagnosis["repair_reason"] = "Enabling the adapter will restore connectivity."
                    diagnosis["risk"] = "low"
                elif not data.get("wifi_present") and data.get("wlan_service", "").lower() != "running":
                    diagnosis["likely_causes"] = ["The WLAN AutoConfig service is not running."]
                    diagnosis["repair_id"] = "restart_wlan"
                    diagnosis["repair_reason"] = "Starting the WLAN service is required for Wi-Fi."
                    diagnosis["risk"] = "low"
                else:
                    diagnosis["likely_causes"] = ["Network configuration failed (DHCP/DNS issue)."]
                    diagnosis["repair_id"] = "ip_renew"
                    diagnosis["repair_reason"] = "Releasing and renewing IP can fix DHCP issues."
                    diagnosis["risk"] = "low"

        elif cat == "crash":
            crashes = data.get("recent_crashes", [])
            if crashes:
                diagnosis["summary"] = f"Detected {len(crashes)} recent system crashes."
                diagnosis["likely_causes"] = ["Recent system errors or unexpected shutdowns."]
                diagnosis["evidence"] = [f"Event ID {c.get('Id')} from {c.get('ProviderName')}" for c in crashes[:2]]
                diagnosis["confidence"] = "medium"
                diagnosis["cannot_fix"] = True
                
        elif cat == "camera":
            if status == "healthy":
                diagnosis["summary"] = "FixIt AI can detect your camera and Windows reports it as working normally."
            else:
                if not data.get("camera_present"):
                    diagnosis["summary"] = "Windows could not detect a camera device."
                    diagnosis["likely_causes"] = ["Camera disabled in firmware", "Physical privacy shutter", "Driver missing", "Hardware disconnected"]
                    diagnosis["cannot_fix"] = True
                elif data.get("driver_status") == "error" or data.get("device_status") == "error":
                    diagnosis["summary"] = "Windows detected the camera, but the device is reporting a driver or device error."
                    diagnosis["likely_causes"] = ["The camera driver has failed or corrupted."]
                    diagnosis["cannot_fix"] = True
                elif data.get("device_status") == "disabled":
                    diagnosis["summary"] = "Windows detected the camera, but the device is disabled."
                    diagnosis["likely_causes"] = ["The camera was disabled in Device Manager."]
                    diagnosis["repair_id"] = "enable_camera"
                    diagnosis["repair_reason"] = "Enabling the device can restore camera functionality."
                else:
                    diagnosis["summary"] = "Camera issue detected but specific cause is unknown."
                    diagnosis["cannot_fix"] = True
                
        elif cat == "bluetooth":
            if data.get("driver_status") == "error":
                diagnosis["summary"] = "Bluetooth driver is reporting an error."
                diagnosis["evidence"] = ["Bluetooth adapter detected", "Driver reporting error"]
                diagnosis["likely_causes"] = ["The Bluetooth driver has failed or corrupted."]
                diagnosis["cannot_fix"] = True
            elif not data.get("service_running"):
                diagnosis["summary"] = "Bluetooth service is stopped."
                diagnosis["evidence"] = ["Bluetooth adapter detected", "Service stopped"]
                diagnosis["repair_id"] = "restart_bluetooth"
                diagnosis["repair_reason"] = "Restarting the service will enable connectivity."

        elif cat == "audio":
            if not data.get("service_running"):
                diagnosis["summary"] = "Windows Audio service is not running."
                diagnosis["evidence"] = ["Audio device detected", "Service stopped"]
                diagnosis["repair_id"] = "restart_audio"
                diagnosis["repair_reason"] = "Restarting the Windows Audio service."
                
        else:
            if status == "error" or status == "problem":
                diagnosis["summary"] = f"Issue detected with {cat}."
                diagnosis["likely_causes"] = ["System reports an issue."]
                diagnosis["cannot_fix"] = True

        return diagnosis


class OllamaBackend(InferenceBackend):
    def __init__(self, ollama_url="http://localhost:11434", model_name="phi3"):
        self.ollama_url = os.getenv("OLLAMA_URL", ollama_url)
        self.model_name = os.getenv("OLLAMA_MODEL", model_name)
        self.available = self._check_availability()
        
        self.system_prompt = """You are FixIt AI, an offline Windows troubleshooting technician.
Rules:
- Use ONLY the diagnostic evidence provided.
- Do NOT invent hardware information or error codes.
- Distinguish evidence from inference.
- Do NOT claim certainty without evidence.
- NEVER recommend destructive actions unnecessarily.
- NEVER generate executable commands.
- Select ONLY repair IDs supplied in the valid repair catalog.
- Explain the issue in simple language.
- Set cannot_fix to true if local software troubleshooting is insufficient.
- The laptop has NO internet connection, do NOT recommend "search online".
- If the status is "unavailable", output "Diagnostic Unavailable." as the summary and set cannot_fix to true.
- If the status is "unknown", output "Windows diagnostic command failed." as the summary and set cannot_fix to true.
- You MUST reply with strictly valid JSON matching this schema exactly.

{
    "summary": "1-2 sentence explanation",
    "likely_causes": ["list", "of", "inferences"],
    "evidence": ["list", "of", "facts directly from data"],
    "confidence": "low|medium|high",
    "repair_id": "string ID from the catalog, or null",
    "repair_reason": "why this repair will help",
    "risk": "low|medium|high",
    "cannot_fix": false
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
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    models = [m["name"] for m in data.get("models", [])]
                    if any(self.model_name in m for m in models):
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
            with urllib.request.urlopen(req, timeout=20) as response:
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
            if result_str:
                try:
                    if result_str.startswith("```json"): result_str = result_str[7:]
                    if result_str.endswith("```"): result_str = result_str[:-3]
                        
                    parsed = json.loads(result_str.strip())
                    
                    if "summary" in parsed and "cannot_fix" in parsed:
                        valid = ["enable_wifi", "restart_wlan", "ip_renew", "flush_dns", "restart_audio", "restart_bluetooth", "enable_camera", "restart_spooler", "restart_wuauserv", None]
                        if parsed.get("repair_id") not in valid:
                            parsed["repair_id"] = None
                        return parsed
                except json.JSONDecodeError:
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
    def __init__(self):
        self.backends = {
            "qnn": QNNBackend(),
            "onnx": ONNXBackend(),
            "llm": OllamaBackend(),
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
        for name in ["qnn", "onnx", "llm"]:
            backend = self.backends[name]
            if getattr(backend, 'available', False):
                res = backend.generate(diagnosis_data)
                if res:
                    return res
        return self.backends["rule"].generate(diagnosis_data)
