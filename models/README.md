# Local AI Models for FixIt AI

This directory contains instructions for installing the offline Local LLM backend for FixIt AI.

## Recommended Model

For offline laptop diagnostics (especially during the hackathon MVP), we recommend using a small, quantized instruct model that fits into standard RAM without crushing the system.

**Model:** `Llama-3-8B-Instruct` (Quantized to 4-bit) or `Phi-3-Mini-4k-Instruct` (Quantized)
**Model Size:** ~2GB to ~5GB
**Memory Requirements:** ~4GB to 8GB of free RAM

## Supported Backends

1. **CPU/GPU (Current Fallback):** Ollama / ONNX Runtime (CPU)
2. **Qualcomm Snapdragon NPU (Future):** Qualcomm Neural Processing SDK (QNN) backend

## Installation Procedure (Ollama approach)

1. Download and install [Ollama](https://ollama.com/) for Windows.
2. Open PowerShell and run:
   ```bash
   ollama run phi3
   ```
3. FixIt AI will automatically detect if the Ollama endpoint (`http://localhost:11434`) is available on startup and switch to the `LocalLLMBackend`.

## Offline Usage

Once the model is downloaded via `ollama run phi3`, you can completely disconnect from the internet. The inference runs entirely locally on your machine. FixIt AI will send structured diagnostic JSON to the model prompt and parse the output, never sending raw PowerShell commands to be hallucinated.

If the model server is stopped, FixIt AI will transparently fall back to the `RuleBasedBackend`.
