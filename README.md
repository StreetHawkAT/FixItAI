# FixIt AI 🛠️

> **"What if your laptop could troubleshoot itself?"**  
> When a laptop breaks, the first thing we usually do is search online. But what if the problem is the internet itself? **FixIt AI** acts as your local, **offline-first** technician. It gathers native Windows telemetry, uses local reasoning to diagnose the root cause, offers predefined safe repairs, and automatically verifies if the fix worked.

---

## 🎯 Project Overview

FixIt AI is an **offline-first**, AI-powered Windows desktop troubleshooting and recovery assistant. Its core diagnostic and reasoning workflow is designed to operate locally, without requiring an internet connection during diagnosis. 

Instead of treating the AI as an uncontrolled command line prompt, FixIt AI enforces a strict safety boundary:

```text
Windows Native Diagnostics
        ↓
Structured Evidence
        ↓
Local AI / Rule-Based Fallback
        ↓
Validated repair_id
        ↓
Allowlisted Repair Engine
        ↓
Fresh Diagnostic Verification
```

### 🛑 The Safety Boundary
The AI **cannot** generate or execute arbitrary PowerShell commands. It can only select predefined allowlisted **repair_id** strings. The underlying execution engine handles the actual repair safely.

---

## 🏆 Snapdragon AI Lab Challenge

This project was built for the **Snapdragon® AI Lab Build & Present Challenge**.

- **Current Development/Test Platform:** x64 Intel Windows.
- **Snapdragon Target:** The architecture was explicitly designed to support Windows on ARM / Snapdragon X Elite PCs.
- **AI Backend:** The system currently uses Ollama (running locally on `localhost:11434` with the `phi3` or `llama3` model) paired with a deterministic **Rule-Based Fallback**.
- **Future NPU Acceleration:** **ONNXBackend** and **QNNBackend** are structurally integrated stubs / future deployment paths explicitly designed to execute models directly on the Qualcomm Hexagon NPU.

---

## 🔍 Diagnostic Categories & Features

FixIt AI features **16 fully implemented** native Windows diagnostic modules. The system never relies on "fake" telemetry. When a diagnostic cannot reliably execute or find data, it explicitly returns `UNKNOWN` or `DIAGNOSTIC UNAVAILABLE` rather than falsely reporting "System Healthy".

| Category | Windows Telemetry Checked | Automated Repair Available? |
|----------|---------------------------|-----------------------------|
| **Network** | Wi-Fi/Ethernet PnP, DHCP, IP config, WLAN service | **YES** (`enable_wifi`, `restart_wlan`, `ip_renew`, `flush_dns`) |
| **Audio** | AudioSrv, AudioEndpointBuilder, Media PnP devices | **YES** (`restart_audio`) |
| **Bluetooth** | bthserv, Bluetooth Support Service, PnP devices | **YES** (`restart_bluetooth`) |
| **Display** | GPU drivers, Monitor presence | *Diagnosis Only* |
| **Keyboard** | HID/PnP status, Device errors | *Diagnosis Only* |
| **Mouse/Touchpad** | HID/PnP status, Device errors | *Diagnosis Only* |
| **Camera** | Image/Camera PnP status, Disabled states | **YES** (`enable_camera`) |
| **Microphone** | AudioSrv, Media input PnP | *Diagnosis Only* |
| **USB** | USB controllers, Code 10/43 device errors | *Diagnosis Only* |
| **Printer** | Print Spooler service, Installed printer queues | **YES** (`restart_spooler`) |
| **Battery** | Win32_Battery (Charge %, AC State, Critical capacity) | *Diagnosis Only* |
| **Storage** | Fixed logical drives, Critical <5% free space limits | *Diagnosis Only* |
| **Performance** | CPU LoadPercentage, FreePhysicalMemory | *Diagnosis Only* |
| **Drivers** | Scans all Device Manager classes for active errors | *Diagnosis Only* |
| **Windows** | wuauserv, Recent System Event Log critical errors | **YES** (`restart_wuauserv`) |
| **Crash** | Kernel-Power, BugChecks, Unexpected Shutdowns | *Diagnosis Only* |

---

## 🛡️ Allowlisted Repair Engine

The **Execution** is completely sandboxed. The currently implemented safe repairs are:

- `enable_wifi` (Enable NetAdapter)
- `restart_wlan` (Restart WlanSvc)
- `ip_renew` (Release/Renew DHCP)
- `flush_dns` (Flush DNS cache)
- `enable_camera` (Enable PnP Device)
- `restart_audio` (Restart AudioSrv)
- `restart_bluetooth` (Restart bthserv)
- `restart_spooler` (Restart Print Spooler)
- `restart_wuauserv` (Restart Windows Update service)

**Verification:** Simply executing a repair does not mean the system is fixed. The application forces a secondary validation check by re-running the original hardware diagnostic. 

---

## 💻 User Interface (Streamlit)

The application features a modern, premium UI organized into the following areas:
- **Overview:** General system health, OS architecture, and AI backend status.
- **Diagnose ("What's Wrong?"):** A 16-category grid to trigger specific subsystem **Diagnosis**, plus a "Full Laptop Diagnosis" button that executes every module asynchronously.
- **Troubleshoot:** The analysis screen rendering the AI's **Reasoning**, evidence lists, and safe **Resolution** buttons.
- **Offline Demo Mode:** A dropdown menu available on the Diagnose page. It allows judges/users to inject simulated hardware failure JSON to safely test the AI reasoning and UI flow without actually breaking their physical laptop.

---

## 🏗️ Technical Stack

- **UI:** Streamlit, custom CSS injects
- **Hardware Telemetry:** `psutil`, `wmi`, `pywin32`, native Windows PowerShell subprocesses (`Get-PnpDevice`, `Get-Service`, etc.)
- **AI Backend:** `urllib` (zero heavy API dependencies), Python standard `json`
- **Testing:** `pytest` 

---

## 🚀 Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/StreetHawkAT/FixItAI.git
   cd FixItAI
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python -m streamlit run app.py
   ```

*(Optional: FixIt AI will seamlessly fall back to a deterministic rule-based engine if an AI backend is not detected. If you wish to use the local LLM, download [Ollama](https://ollama.com/), start it on `localhost:11434`, and pull the `phi3` or `llama3` model).*

---

## 🧪 Testing

The repository contains a robust testing suite leveraging `unittest.mock` to simulate PowerShell outputs, preventing accidental modifications to your host machine during tests.

Currently, **29 tests** pass successfully, covering:
- All 16 hardware diagnostic parsers
- RuleBased engine fallbacks
- Integration schemas and state clearing
- The isolated repair engine registry

To run the test suite:
```powershell
python -m pytest tests\
```

---
*Developed as an offline-first solution for native Windows reliability.*
