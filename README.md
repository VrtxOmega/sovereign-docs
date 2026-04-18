# SOVEREIGN DOCS

**Unified offline-first document generation and intelligence platform for the VERITAS ecosystem.**

<img width="2080" height="1350" alt="Screenshot 2026-04-18 023700" src="https://github.com/user-attachments/assets/f388944d-4c0f-49a5-aae2-08403fe42c04" />
<img width="2082" height="1345" alt="Screenshot 2026-04-18 023719" src="https://github.com/user-attachments/assets/1ae5d6cd-9acd-49ab-9f35-a55228414ef2" />





---

## OVERVIEW

Sovereign Docs consolidates three legacy VERITAS systems — the PDF Generator, Reporter, and Morning Brief — into a single isolated desktop module. It is a hybrid Electron + Python Flask application that takes any input (text, markdown, uploaded documents, or scraped URLs), processes it through a local AI analysis pipeline, and exports it simultaneously into 7 standardized formats with cryptographic provenance stamping.

The Python backend runs on port `5070` as a fully decoupled REST API — other scripts, agents, and ecosystem tools can call it headlessly without ever opening the UI.

> **Zero cloud. Zero CDN. Everything runs on your hardware.**

---

## FEATURES

- **7-Format Export Engine** — Simultaneously compiles input into PDF, DOCX, HTML, Markdown, TXT, Slides, and Auto-Receipt in parallel. PDF exports include cryptographic QR provenance stamps and confidentiality watermarks. Every export generates a unique Trace ID.
- **Document Analysis Engine** — Drag-and-drop document parsing for `.md`, `.txt`, `.json`, `.docx`, `.pdf`, and `.csv`. Routes content through local LLM containers (qwen3:8b) via `analyze_engine.py` to refine grammar, rewrite sections, or analyze structure before final compilation.
- **Intelligence Briefing Dashboard** — Connects directly to the local Vault to synthesize Daily Briefs, Weekly Rollups, or Custom Briefs across configurable date ranges and sources. Extracts actionable intelligence from Moltbook data into automated executive summaries.
- **Live Markdown Editor** — Split-pane editor with real-time preview rendering. Import files or start from blank. Classification tagging (Internal, Confidential, Public). Direct export from editor to any format.
- **Document Library** — Persistent local library of all generated documents with search and retrieval.
- **Headless REST API** — The Flask backend is fully decoupled from the UI. Programmatic access via `/api/export`, `/api/upload`, `/api/scrape_url`, and `/api/refine` endpoints. Any script or agent in the ecosystem can generate documents without touching the desktop app.
- **Cryptographic Provenance** — Every export operation generates a Trace ID (`VD-YYYY-MM-DD-XXXXXXXX`) linking the output to its source material, export parameters, and operation manifest.
- **Auto-Receipt Generation** — Unforgeable cryptographic receipt containing output hashes, Trace ID, and a complete operation manifest for audit chain integrity.

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│                    SOVEREIGN DOCS                       │
│              Electron Desktop Application               │
└──────────────────────────┬──────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
   │   Shell UI    │ │  Brief Engine │ │  Analyze      │
   │               │ │               │ │  Engine       │
   │  4-Tab Layout │ │  Vault Sync   │ │               │
   │  Create       │ │  Moltbook     │ │  Local LLM    │
   │  Analyze      │ │  Extraction   │ │  (qwen3:8b)   │
   │  Brief        │ │  Daily/Weekly │ │  Grammar      │
   │  Library      │ │  Custom       │ │  Rewrite      │
   └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                     IPC / localhost
                             │
                  ┌──────────▼──────────┐
                  │   Python Backend    │
                  │   Flask on :5070    │
                  │                     │
                  │  Doc Export Engine  │
                  │  7-format parallel  │
                  │  PyPDF / Jinja2     │
                  │  QR Provenance      │
                  │  Trace ID Gen       │
                  │  REST API           │
                  └─────────────────────┘
```

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Shell UI** | Electron / JS | 4-tab dashboard (Create, Analyze, Brief, Library) with VERITAS gold-and-obsidian aesthetic |
| **Doc Export Engine** | Python / PyPDF / Jinja2 | 7 unified export pipelines with cryptographic provenance stamping |
| **Brief Engine** | Python | Vault synthesis engine extracting intelligence from Moltbook data into automated briefings |
| **Analyze Engine** | Python / Ollama | Local LLM document analysis, grammar refinement, and structural rewriting |
| **Backend API** | Flask | Internal REST API on port `5070` serving `/api/export`, `/api/upload`, `/api/scrape_url`, `/api/refine` |

---

## QUICKSTART

### Prerequisites

- Node.js 18+
- Python 3.10+
- Ollama with `qwen3:8b` (for document analysis features)

### 1. Initialize Backend

```bash
cd backend
pip install -r requirements.txt
python server.py
# Flask server starts on http://127.0.0.1:5070
```

### 2. Launch Electron App

In a separate terminal:

```bash
npm install
npm start
```

### REST API (Headless Mode)

The backend runs independently. Send requests directly without the UI:

```bash
# Export a document
curl -X POST http://localhost:5070/api/export \
  -H "Content-Type: application/json" \
  -d '{"content": "# My Document\nContent here.", "formats": ["pdf", "md"]}'

# Upload and parse a file
curl -X POST http://localhost:5070/api/upload \
  -F "file=@document.pdf"

# AI-powered refinement
curl -X POST http://localhost:5070/api/refine \
  -H "Content-Type: application/json" \
  -d '{"content": "Draft text to refine.", "mode": "grammar"}'
```

---

## EXPORT FORMATS

| Format | Output | Features |
|--------|--------|----------|
| **PDF** | `.pdf` | QR provenance stamp, confidentiality watermark, classification header |
| **DOCX** | `.docx` | Strict hierarchical markdown formatting preserved |
| **HTML** | `.html` | Standalone rendered document |
| **Markdown** | `.md` | Pure text with formatting |
| **TXT** | `.txt` | Plain text extraction |
| **Slides** | `.pptx` | Auto-paged presentation layout |
| **Auto-Receipt** | `.json` | Cryptographic receipt: output hashes, Trace ID, operation manifest |

---

## SECURITY & SOVEREIGNTY

- **Offline-only.** No cloud services, no CDN dependencies, no external API calls for core functionality.
- **Local AI.** Document analysis runs through local Ollama containers — no text leaves the machine.
- **Cryptographic tracing.** Every export operation generates a unique Trace ID linking output to source material and parameters.
- **Decoupled backend.** The Flask API runs independently, sandboxed on localhost with no external network surface.
- **No telemetry.** Zero analytics, zero usage tracking, zero data collection.

---

## OMEGA UNIVERSE

Sovereign Docs is one node in the VERITAS & Sovereign Ecosystem:

| Repository | Role |
|-----------|------|
| [omega-brain-mcp](https://github.com/VrtxOmega/omega-brain-mcp) | Central intelligence — 10-gate VERITAS pipeline, cross-session memory, cryptographic audit ledger |
| [Ollama-Omega](https://github.com/VrtxOmega/Ollama-Omega) | Sovereign Ollama bridge — local and cloud model inference via MCP |
| [veritas-vault](https://github.com/VrtxOmega/veritas-vault) | Local-first AI knowledge retention engine — feeds briefing data into Sovereign Docs |
| [Gravity-Omega](https://github.com/VrtxOmega/Gravity-Omega) | Sovereign AI-powered IDE — development environment for the entire ecosystem |
| [aegis-rewrite](https://github.com/VrtxOmega/aegis-rewrite) | AI-powered code remediation and security scanning |

---

## LICENSE

MIT — see [LICENSE](LICENSE) for full terms.

---

Built by [RJ Lopez](https://github.com/VrtxOmega) — VERITAS & Sovereign Ecosystem
