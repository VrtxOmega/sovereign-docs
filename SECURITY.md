# Security Policy — Sovereign Docs

## Sovereignty Guarantees

Sovereign Docs is designed to operate **entirely offline**. These guarantees are architectural, not configurable:

- **No cloud services.** The application makes zero outbound network calls for core functionality. No analytics, no telemetry, no CDN.
- **Local AI only.** Document analysis runs through local Ollama containers (`qwen3:8b`). No text, document content, or metadata leaves the machine.
- **No tracking.** Zero usage analytics, zero error reporting services, zero data collection of any kind.
- **Decoupled backend.** The Flask API binds exclusively to `127.0.0.1:5070` — it is unreachable from the network.
- **Cryptographic provenance.** Every export generates a unique Trace ID (`VD-YYYY-MM-DD-XXXXXXXX`) and an optional Auto-Receipt containing SHA-256 hashes of all output files.

## Reporting a Vulnerability

If you discover a security issue, please report it via email to VrtxOmega@pm.me. Do not open a public issue.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ |
| < 1.0   | ❌ |

## Dependencies

The application has a single Node.js dependency (Electron). Python dependencies are listed in `backend/requirements.txt`. All packages are pinned to specific versions.

## SSWP Attestation

This repository carries an SSWP cryptographic attestation (`.sswp.json`) verifying dependency integrity, build determinism, and adversarial probe results.

---

*VERITAS Ω — Sovereign Infrastructure*
