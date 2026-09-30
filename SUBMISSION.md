# FixIt AI - Snapdragon AI Lab Challenge Submission

## Project Overview

**FixIt AI** is a privacy-first, on-device AI assistant for PC diagnostics and troubleshooting. It analyzes battery health, detects critical system events from Windows logs, and provides evidence-based recommendations — all while keeping data completely local on the user's Snapdragon-powered PC.

---

## Key Features

### 🔋 Battery Health Analysis
- **Report Parsing**: Parse Windows battery reports generated via `powercfg /batteryreport`
- **Health Assessment**: Calculate battery health percentage from design vs. full charge capacity
- **Cycle Count Monitoring**: Track battery wear through charge cycle analysis
- **Power Consumption Alerts**: Detect unusually high discharge rates
- **Trend Tracking**: Compare reports over time to monitor degradation

### 📋 Windows Event Log Analysis
- **Critical Event Detection**: Identify kernel-power failures, unexpected shutdowns, and driver crashes
- **Pattern Recognition**: Count recurring error sources and event IDs
- **Crash Analysis**: Isolate application crashes and DCOM permission issues
- **Severity Classification**: Categorize events as informational, warning, or critical

### 📊 Diagnostic Intelligence
- **Persistent History**: Store all diagnostic findings in a local SQLite database
- **Evidence-Based Recommendations**: Actionable troubleshooting steps tied to specific findings
- **Comparison Analysis**: Compare battery health across multiple report uploads
- **Status Tracking**: Mark investigations as open or resolved

---

## Why FixIt AI?

### Problem It Solves
1. **PC Troubleshooting Is Hard**: Battery drain, crashes, and errors are difficult for average users to diagnose
2. **Information Overload**: Windows event logs contain thousands of entries — users can't parse them manually
3. **Privacy Concerns**: Cloud-based diagnostic tools require uploading sensitive system data

### Our Solution
An on-device AI diagnostics assistant that:
- Analyzes battery reports and event logs without sending data anywhere
- Provides clear, actionable recommendations in plain language
- Remembers diagnostic findings to track trends over time
- Runs entirely on Snapdragon-powered hardware

---

## Technical Architecture

### Technology Stack
- **Frontend**: Streamlit (Python)
- **Backend**: Python 3.8+
- **Database**: SQLite
- **Report Parsing**: BeautifulSoup, regex
- **System Diagnostics**: psutil
- **Target Platform**: Snapdragon NPU

### System Architecture

```
┌─────────────────────────────────────────┐
│          FixIt AI Dashboard             │
│           (Streamlit UI)                │
└───────────┬─────────────────────────────┘
            │
            ├──────────────┬──────────────┐
            │              │              │
      ┌─────▼─────┐  ┌────▼────┐  ┌─────▼─────┐
      │  Battery  │  │   Log   │  │  Database │
      │  Analyzer │  │ Analyzer│  │  Manager  │
      └─────┬─────┘  └────┬────┘  └─────┬─────┘
            │              │              │
            └──────────────┴──────────────▼
                  ┌──────────────┐
                  │   SQLite     │
                  │ Local Storage│
                  └──────────────┘
```

### Snapdragon Optimization Strategy

**Current Implementation:**
- Efficient local processing with Python
- Lightweight SQLite storage
- Optimized HTML and text parsing

**Snapdragon Deployment Path:**
1. Convert diagnostic analysis models to ONNX format
2. Use Qualcomm AI Hub for NPU optimization
3. Leverage Snapdragon Neural Processing SDK for inference acceleration
4. Implement power-efficient background monitoring via Hexagon DSP
5. Use Qualcomm AI Engine Direct for real-time system health scoring

---

## Use Cases

### Use Case 1: Diagnose Battery Issues
**Scenario**: "My laptop battery drains too quickly"

**Solution**:
1. Generate battery report: `powercfg /batteryreport`
2. Upload to FixIt AI
3. Get analysis:
   - Battery health: 78%
   - High discharge rate detected
   - Recommendations: Close background apps, reduce brightness, check for power-hungry processes

### Use Case 2: Investigate System Crashes
**Scenario**: "My laptop keeps restarting unexpectedly"

**Solution**:
1. Export Windows event log from Event Viewer
2. Upload to FixIt AI
3. Get analysis:
   - 5 Kernel-Power (Event 41) events detected
   - Recommendations: Check power settings, verify cooling, update drivers

### Use Case 3: Track Computer Health Over Time
**Scenario**: "Is my battery getting worse?"

**Solution**:
1. FixIt AI stores all diagnostic history
2. Compare reports from different dates
3. See: "Battery health decreased by 3.5% over 2 weeks"
4. Get proactive recommendations before issues become critical

---

## Demo Walkthrough

### 1. Dashboard Overview
- Clean, modern interface with green-themed branding
- Quick action buttons for Battery Check and Event Log Analysis
- Real-time diagnostic statistics

### 2. Battery Analysis
- Upload Windows battery report
- Detailed health analysis with color-coded severity
- Actionable recommendations

### 3. Event Log Analysis
- Upload exported event logs
- Critical event detection with occurrence counts
- Error source breakdown and troubleshooting steps

### 4. Diagnostic History
- Persistent tracking of all analyses
- Status indicators (open / resolved)
- Time-stamped entries for trend monitoring

---

## Impact & Benefits

### For Users
- Understand PC problems without technical expertise
- Get actionable troubleshooting steps instantly
- Track computer health over time
- Keep all diagnostic data private on-device

### For Snapdragon Platform
- Demonstrates practical on-device AI use case
- Showcases NPU capabilities for real-time analysis
- Privacy-focused edge computing showcase
- Practical daily-use application for Snapdragon PC owners

---

## Future Enhancements

### Phase 2 (Post-Competition)
- [ ] Real-time system monitoring dashboard
- [ ] Automatic battery report generation and analysis
- [ ] Integration with Windows Task Scheduler for periodic checks
- [ ] Local LLM integration (Ollama/Llama) for natural language Q&A

### Phase 3 (Advanced)
- [ ] Predictive maintenance warnings
- [ ] Custom AI model fine-tuning on diagnostic patterns
- [ ] Voice interface for hands-free troubleshooting
- [ ] Hardware sensor monitoring (temperature, fan speed)

### Snapdragon-Specific
- [ ] Quantized diagnostic models for NPU
- [ ] Power-efficient background monitoring
- [ ] Hardware-accelerated log parsing
- [ ] Real-time system health scoring via AI Engine Direct

---

## Installation & Setup

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

**Quick Start:**
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Competition Criteria Alignment

### Technical Implementation
- Clean, modular Python architecture
- Efficient local processing with SQLite storage
- Structured analysis pipeline for battery and event logs
- Optimized for Snapdragon deployment

### Application Use Case & Innovation
- Novel approach to on-device PC diagnostics
- Combines battery analysis + event log parsing in one tool
- Evidence-based recommendations from structured data analysis
- Persistent diagnostic history for trend tracking

### Deployment & Accessibility
- One-command installation and launch
- No cloud dependency — fully offline capable
- Works on any Windows PC, optimized for Snapdragon
- Intuitive Streamlit UI requires no technical expertise

### Presentation & Documentation
- Comprehensive README and QUICKSTART guide
- Clean code with docstrings and comments
- Architecture diagrams and use case examples
- Competition submission document

---

## Development Timeline

- **Day 1**: Project planning and architecture design
- **Day 2**: Core functionality (database, battery analyzer)
- **Day 3**: Event log analysis and diagnostic intelligence
- **Day 4**: UI development and integration
- **Day 5**: Testing, refinement, demo recording

---

## License

MIT License - See LICENSE file for details

---

## Acknowledgments

Built for the **Snapdragon® AI Lab Build & Present Challenge 2026**

Special thanks to Qualcomm for providing the platform and opportunity to build innovative AI solutions.

---

## Contact

**Project**: FixIt AI  
**Challenge**: Snapdragon AI Lab 2026  
**Status**: MVP Complete  

---

**FixIt AI** - Your AI-Powered PC Troubleshooting Companion  
*Privacy-first. Local-first. Snapdragon-powered.*
