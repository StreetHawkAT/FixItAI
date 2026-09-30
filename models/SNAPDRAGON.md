# Snapdragon Deployment Path (Hackathon Notes)

FixIt AI is designed with an AI backend abstraction (`InferenceBackend`) that cleanly isolates execution environments. 

## Development Implementation (Current)
Currently, `OllamaBackend` runs on the local CPU (via Intel x64 / ARM64). The logic, prompting, JSON schema enforcement, and repair loops are 100% identical to how the NPU version will behave.

## Snapdragon Hardware Validation (Future QNNBackend)

To enable **Qualcomm NPU Acceleration** on Snapdragon X Elite / X Plus hardware, the following path must be validated on physical silicon:

### 1. Required SDKs & Runtimes
- **Qualcomm Neural Processing SDK (QNN)** for Windows on Snapdragon.
- Alternately, **ONNX Runtime (ORT)** with the QNN Execution Provider (EP).

### 2. Supported Model Format
- Models must be quantized to INT4 or INT8 using Qualcomm's AI Engine Direct (QNN) or ONNX format.
- Recommended quantization tool: Qualcomm AI Hub / Qualcomm Model Optimizer (QMO).

### 3. Execution Pipeline
- The `QNNBackend` or `ONNXBackend` in `core/ai_engine.py` will load the quantized model (e.g. `phi3.onnx`).
- Inference requires initializing the `onnxruntime.InferenceSession` with `providers=['QNNExecutionProvider']`.

### 4. Verification
- True NPU execution must be validated on the device by checking the Windows Task Manager (NPU usage graph) or by observing sub-100ms first-token latency with low CPU overhead.
- **IMPORTANT**: FixIt AI does not falsely claim NPU acceleration. The UI currently correctly reports `AI Acceleration: Not detected` or `Snapdragon NPU unavailable` unless explicitly running the QNN/ONNX bindings on Snapdragon silicon.

## Summary
The software architecture is **Snapdragon-ready**. The business logic, strict JSON control, and offline recovery flows are fully complete. Finalizing NPU support only requires swapping the `OllamaBackend` stub with `QNNBackend` once physical testing hardware is acquired.
