<div align="center">

# Ω Sovereign Docs

[![Status](https://img.shields.io/badge/Status-Active-gold?style=for-the-badge&labelColor=1a1a1a&color=d4af37)](#)
[![Python](https://img.shields.io/badge/Python-3.14+-gold?style=for-the-badge&labelColor=1a1a1a&color=d4af37)](#)
[![Electron](https://img.shields.io/badge/Electron-v33-gold?style=for-the-badge&labelColor=1a1a1a&color=d4af37)](#)
[![VERITAS](https://img.shields.io/badge/Standard-VERITAS-gold?style=for-the-badge&labelColor=1a1a1a&color=d4af37)](#)

*The unified, offline-first document generation and intelligence platform for the VERITAS ecosystem.*

</div>

---

## 🏛️ Architecture Overview

Sovereign Docs consolidates the legacy VERITAS PDF Generator, Reporter, and Morning Brief mechanisms into an isolated, sovereign desktop module.

| Module | Purpose | Stack |
|--------|---------|-------|
| **Doc Engines** | 7 unified export pipelines (PDF, DOCX, HTML, MD, TXT, Slides, Auto-Receipt). | Python / PyPDF / Jinja2 |
| **Brief Engine** | Vault synthesis engine extracting intelligence from Moltbook data. | Python |
| **Backend** | Internal Flask API serving endpoints on port `5070`. | Flask |
| **Shell UI** | Native desktop client featuring a 4-tab dashboard (Create, Analyze, Brief, Library). | Electron / JS |

---

## ✨ Features

- **7-Format Export Engine**: Automatically orchestrate complex source data into standardized exports instantly.
- **Sovereign Briefing Dashboard**: Direct integration with Moltbook data to synthesize auto-generated executive intelligence briefs.
- **Cryptographic Provenance**: Hardened PDF generator supporting QR provenance stamping and active confidentiality watermarks.
- **VERITAS Aesthetics**: Native dark-mode gold-and-obsidian UI layout built directly into the client.
- **Unified Local Interface**: Fast, sandboxed execution with absolute zero cloud dependencies.

---

## 🚀 Quick Start

### 1. Initialize Backend (Terminal 1)
```powershell
# Navigate to the backend directory
cd backend

# Launch the Flask server on Port 5070
python server.py
```

### 2. Launch Interface (Terminal 2)
```powershell
# In the root, install Node dependencies (if required)
npm install

# Boot the Electron Shell
npm start
```
*Alternatively, double-click the `SovereignDocs.vbs` launcher on Windows for a silent background boot.*

---

<div align="center">
  <br>
  <b>Built by RJ Lopez | VERITAS Framework</b>
</div>
