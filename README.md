# FixIt AI 🛠️

**FixIt AI** is an offline-first, AI-powered Windows desktop troubleshooting and recovery assistant. Built as a submission for the **Snapdragon® AI Lab Build & Present Challenge**, FixIt AI acts as your personal laptop technician that works perfectly **even when your internet is completely disconnected.**

## 🎯 The Problem & Innovation

When a laptop's Wi-Fi breaks, or a critical driver crashes, users are left stranded. They cannot Google the solution or ask cloud-based AI for help because their device has no internet access. 

**FixIt AI solves this by running entirely locally on Snapdragon-powered PCs.** 
By leveraging the power of local AI models (via Qualcomm AI Hub / ONNX / Ollama) and native Windows hardware telemetry, FixIt AI can:
1. **Diagnose** hardware and software failures instantly.
2. **Explain** the problem in simple, human-readable language using a local LLM.
3. **Repair** the issue securely using pre-approved, safe PowerShell actions.
4. **Verify** that the fix actually worked.

## 🏆 Snapdragon AI Lab Challenge Alignment

This project is specifically designed to leverage the capabilities of **Snapdragon-powered HP PCs**:

- **Technical Implementation:** Combines 16 distinct native Windows PnP/WMI hardware diagnostic modules with a robust Local AI reasoning engine. The AI output is strictly schema-bound, ensuring it never hallucinates unsafe executable code.
- **Application Use Case:** An essential utility for every PC user. The concept of an "offline AI recovery assistant" perfectly demonstrates the unique value of powerful on-device NPU inference.
- **Deployment & Accessibility:** Features a premium, accessible UI built in Streamlit. It runs seamlessly on Windows on ARM without requiring cloud API keys or subscriptions.

## ⚙️ Core Capabilities

FixIt AI features **16 fully implemented diagnostic modules**, capturing structured telemetry across the entire system:

| Subsystem | Real Diagnostics | AI Reasoning | Safe Automated Repair |
|-----------|------------------|--------------|-----------------------|
| 🌐 Network | ✅ | ✅ | ✅ (Enable Wi-Fi, Reset DHCP, Flush DNS) |
| 🔊 Audio | ✅ | ✅ | ✅ (Restart AudioSrv) |
| ᛒ Bluetooth | ✅ | ✅ | ✅ (Restart bthserv) |
| 📷 Camera | ✅ | ✅ | ✅ (Enable PnP Device) |
| 🖨️ Printer | ✅ | ✅ | ✅ (Restart Spooler) |
| 🪟 Windows | ✅ | ✅ | ✅ (Restart Update Service) |
| 🖥️ Display | ✅ | ✅ | ❌ (Diagnosis Only) |
| ⌨️ Keyboard | ✅ | ✅ | ❌ (Diagnosis Only) |
| 🔋 Battery | ✅ | ✅ | ❌ (Diagnosis Only) |
| 💾 Storage | ✅ | ✅ | ❌ (Diagnosis Only) |

*(Includes comprehensive modules for Performance, Crash Logs, Microphone, Mouse/Touchpad, USB, and General Drivers).*

## 🏗️ Architecture

```text
USER INTERFACE
  ↓ (User clicks "Check Camera")
NATIVE WINDOWS DIAGNOSTIC (PowerShell / WMI / PnP)
  ↓ (Generates structured hardware evidence)
AI ENGINE (Local LLM / Rule-Based Fallback / QNN)
  ↓ (Validates strictly formatted JSON schema)
REPAIR REGISTRY 
  ↓ (Maps AI decision to predefined safe lambda function)
WINDOWS EXECUTION & RE-VERIFICATION
```

## 🚀 Getting Started

### Prerequisites
- Windows 11 (Optimized for Snapdragon Windows on ARM devices)
- Python 3.10+
- (Optional) Ollama installed locally with `phi3` or `llama3` for full LLM inference.

### Installation

1. Clone the repository and set up your virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Launch the Application:
```powershell
python -m streamlit run app.py
```

### 🧪 Offline Demo Mode
Don't want to actually break your laptop to test the AI? FixIt AI includes a built-in **Offline Demo Mode**. 
Navigate to the "Diagnose" tab, expand the Demo Mode section at the bottom, and instantly inject simulated hardware failures (e.g., *Camera Driver Error*, *Wi-Fi Disabled*) to watch the AI pipeline analyze and resolve the issue in real-time.

## 🛡️ Safety First

FixIt AI operates under a strict security boundary:
- **No Arbitrary Code:** The LLM does *not* generate PowerShell scripts. It only outputs a predefined `repair_id` string.
- **Controlled Execution:** The `RepairEngine` maps that string to hardcoded, rigorously tested PowerShell commands.
- **Privacy:** Diagnostics never leave the device. No cloud telemetry is collected.

## 🤝 Testing
The project includes a comprehensive test suite covering all 16 hardware diagnostic modules and the AI routing engine.
```powershell
python -m pytest tests\
```

---
*Built for the Snapdragon® AI Lab Build & Present Challenge.*
