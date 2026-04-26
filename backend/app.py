"""
VERITAS Docs — Flask Backend
==============================
Unified server for document creation, analysis, and export.
Port: 5070
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

from flask import Flask, request, jsonify, send_file, send_from_directory

# Ensure backend is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from models import BrandPreset, VeritasDocument, SUPPORTED_FORMATS, FORMAT_LABELS
from format_router import export, export_all
from draft_manager import draft_manager


# ── APP SETUP ─────────────────────────────────────────────
app = Flask(__name__,
            static_folder=str(Path(__file__).resolve().parent.parent / "renderer"),
            static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB


# ── ROUTES ────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main application."""
    renderer_dir = Path(__file__).resolve().parent.parent / "renderer"
    return send_from_directory(str(renderer_dir), "index.html")


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files from renderer directory."""
    renderer_dir = Path(__file__).resolve().parent.parent / "renderer"
    return send_from_directory(str(renderer_dir), filename)


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "app": "VERITAS Docs",
        "version": "1.0.0",
        "formats": SUPPORTED_FORMATS,
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/formats")
def list_formats():
    """List available export formats."""
    return jsonify({
        "formats": [
            {"id": fmt, "label": FORMAT_LABELS.get(fmt, fmt)}
            for fmt in SUPPORTED_FORMATS
        ]
    })


@app.route("/api/export", methods=["POST"])
def export_document():
    """
    Export a document to selected formats.

    JSON body:
    {
        "title": "Document Title",
        "subtitle": "Optional subtitle",
        "content": "# Markdown content...",
        "formats": ["pdf", "html", "md"],
        "confidentiality": "internal",
        "source_name": "my_document.md"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "No content provided"}), 400

    formats = data.get("formats", ["pdf"])
    if not formats:
        return jsonify({"error": "No formats specified"}), 400

    # Build document
    doc = VeritasDocument(
        title=data.get("title", "Untitled Document"),
        subtitle=data.get("subtitle"),
        content=content,
        source_type="editor",
        source_name=data.get("source_name", "editor_input.md"),
    )
    doc.compute_source_hash()

    # Build brand preset
    brand = BrandPreset(
        confidentiality=data.get("confidentiality", "internal"),
        watermark=data.get("watermark"),
    )

    try:
        output = export(doc, formats, brand, operation="create")
        return jsonify({
            "success": True,
            "trace_id": output.trace_id,
            "formats": output.formats,
            "hashes": output.hashes,
            "receipt": output.receipt_path,
        })
    except Exception as e:
        return jsonify({"error": f"Export failed: {str(e)}"}), 500


@app.route("/api/upload", methods=["POST"])
def upload_and_export():
    """
    Upload a file and export to selected formats.
    Multipart form: file + formats (comma-separated) + optional fields.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files["file"]
    filename = f.filename or "upload.txt"
    formats = request.form.get("formats", "pdf").split(",")
    formats = [fmt.strip() for fmt in formats if fmt.strip()]

    try:
        file_bytes = f.read()
        from input.file_extractor import extract_text
        content = extract_text(file_bytes, filename)
    except Exception as e:
        return jsonify({"error": f"File read failed: {str(e)}"}), 422
        
    model = request.form.get("model", "")
    if model:
        try:
            from intelligence.analyze_engine import analyze_document, format_analysis_markdown
            analysis_dict = analyze_document(content, model=model)
            content = format_analysis_markdown(analysis_dict, content)
        except Exception as e:
            print(f"[API Upload] AI Analysis failed: {e}")

    doc = VeritasDocument(
        title=request.form.get("title", Path(filename).stem.replace('_', ' ').title()),
        subtitle="AI Intelligence Analysis" if model else request.form.get("subtitle"),
        content=content,
        source_type="file",
        source_name=filename,
    )
    doc.compute_source_hash()

    brand = BrandPreset(
        confidentiality=request.form.get("confidentiality", "internal"),
    )

    try:
        output = export(doc, formats, brand, operation="create")
        return jsonify({
            "success": True,
            "trace_id": output.trace_id,
            "formats": output.formats,
            "hashes": output.hashes,
            "receipt": output.receipt_path,
        })
    except Exception as e:
        return jsonify({"error": f"Export failed: {str(e)}"}), 500


@app.route("/api/scrape_url", methods=["POST"])
def scrape_url():
    """
    Scrape a URL and return its text content as Markdown.
    """
    data = request.get_json()
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
        
    try:
        from input.url_scraper import scrape_url_to_markdown
        markdown_content = scrape_url_to_markdown(url)
        return jsonify({"success": True, "content": markdown_content})
    except Exception as e:
        return jsonify({"error": f"Scrape failed: {str(e)}"}), 500

@app.route("/api/generate_brief", methods=["POST"])
def generate_brief():
    """
    Generate an Intelligence Brief.

    JSON body:
      {
        "type":  "daily" | "weekly" | "custom",
        "start": "YYYY-MM-DD"   (optional, custom only),
        "end":   "YYYY-MM-DD"   (optional, custom only)
      }
    """
    data = request.get_json(silent=True) or {}
    brief_type = (data.get("type") or "daily").strip().lower()
    try:
        from engines.brief_engine import generate_brief as gb
        result = gb(
            brief_type=brief_type,
            start=data.get("start"),
            end=data.get("end"),
        )
        # Always return 200 even on graceful 'offline' so the UI can show the
        # informational stub instead of treating it as a fetch failure.
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "type": brief_type,
            "content": f"# Brief Engine Crashed\n\n```text\n{str(e)}\n```",
            "vault_status": f"error: {e}",
            "post_count": 0,
            "window_label": "",
        }), 500

@app.route("/api/library")
def list_library():
    """
    List all generated documents and receipts, grouped by Trace ID where
    possible. Filenames produced by format_router.py follow the pattern:
        <slug>_<TRACE_ID>.<ext>
    so siblings of a single export share the same trace fragment.
    """
    project_root = Path(__file__).resolve().parent.parent
    doc_dir = project_root / "output" / "documents"
    receipt_dir = project_root / "output" / "receipts"

    documents = []
    if doc_dir.exists():
        for f in sorted(doc_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file():
                documents.append({
                    "name": f.name,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    "format": f.suffix.lstrip('.').lower(),
                    "trace_id": _extract_trace_id(f.name),
                    "slug":     _extract_slug(f.name),
                })

    receipts = []
    if receipt_dir.exists():
        for f in sorted(receipt_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file():
                receipts.append({
                    "name": f.name,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    "trace_id": _extract_trace_id(f.name),
                })

    return jsonify({
        "documents": documents,
        "receipts": receipts,
        "total_documents": len(documents),
        "total_receipts": len(receipts),
    })


# ── Library helpers ─────────────────────────────────────────
import re as _re
_TRACE_RE = _re.compile(r'(VD-\d{4}-\d{2}-\d{2}-[A-F0-9]{8})', _re.IGNORECASE)


def _extract_trace_id(name: str) -> str:
    m = _TRACE_RE.search(name)
    return m.group(1).upper() if m else ""


def _extract_slug(name: str) -> str:
    """Get a human-friendly title slug from a filename."""
    base = Path(name).stem
    # Strip the trace ID and trailing _slides suffix if present.
    base = _TRACE_RE.sub("", base).rstrip("_-")
    if base.endswith("_slides"):
        base = base[:-len("_slides")]
    return base.replace("_", " ").strip() or "Untitled"


@app.route("/api/delete", methods=["POST"])
def delete_files():
    """
    Delete a list of files from the output directory. Refuses to delete
    anything outside <project_root>/output/ as a safety guard.
    """
    data = request.get_json(silent=True) or {}
    paths = data.get("paths") or []
    if not isinstance(paths, list) or not paths:
        return jsonify({"error": "No paths provided"}), 400

    project_root = Path(__file__).resolve().parent.parent
    output_root = (project_root / "output").resolve()

    deleted = []
    skipped = []
    for raw in paths:
        try:
            p = Path(raw).resolve()
            # Refuse anything that escapes the output dir.
            if not str(p).startswith(str(output_root)):
                skipped.append({"path": raw, "reason": "outside output directory"})
                continue
            if not p.exists():
                skipped.append({"path": raw, "reason": "missing"})
                continue
            p.unlink()
            deleted.append(str(p))
        except Exception as e:
            skipped.append({"path": raw, "reason": str(e)})

    return jsonify({"success": True, "deleted": deleted, "skipped": skipped})


@app.route("/api/open/<path:filepath>")
def open_file(filepath):
    """Open a generated file."""
    import shlex
    full_path = Path(filepath)
    if not full_path.exists():
        return jsonify({"error": "File not found"}), 404

    try:
        if os.name == 'nt':
            os.startfile(str(full_path))
        else:
            import subprocess
            subprocess.run(['xdg-open', str(full_path)], check=True)
        return jsonify({"success": True, "path": str(full_path)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/drafts/save", methods=["POST"])
def save_draft():
    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"error": "No content"}), 400
    
    path = draft_manager.save_draft(data["content"], data.get("title", "Untitled"))
    return jsonify({"success": True, "path": path})

@app.route("/api/drafts/latest")
def get_latest_draft():
    draft = draft_manager.get_latest_draft()
    if draft:
        return jsonify({"success": True, "draft": draft})
    return jsonify({"success": False, "error": "No draft found"})
    
@app.route("/api/refine", methods=["POST"])
def refine_text():
    data = request.get_json()
    if not data or "content" not in data or "mode" not in data:
        return jsonify({"error": "Missing content or mode"}), 400
    
    try:
        from intelligence.analyze_engine import refine_document_text
        refined = refine_document_text(data["content"], data["mode"], data.get("model", "qwen3:8b"))
        return jsonify({"success": True, "content": refined})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ollama_status")
def ollama_status():
    """Check if Ollama is reachable and list available models."""
    try:
        import requests as req
        r = req.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return jsonify({"online": True, "models": models})
    except Exception:
        pass
    return jsonify({"online": False, "models": []})


@app.route("/api/import_file", methods=["POST"])
def import_file():
    """
    Import a file and return its extracted text content for the editor.
    Does NOT export — just extracts text from the uploaded file.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files["file"]
    filename = f.filename or "upload.txt"

    try:
        file_bytes = f.read()
        from input.file_extractor import extract_text
        content = extract_text(file_bytes, filename)
        return jsonify({
            "success": True,
            "content": content,
            "filename": filename,
            "size": len(file_bytes),
        })
    except Exception as e:
        return jsonify({"error": f"Import failed: {str(e)}"}), 422


if __name__ == "__main__":
    print("\n  [OMEGA] VERITAS Docs - Backend Server")
    print(f"  Formats: {', '.join(SUPPORTED_FORMATS)}")
    print("  http://localhost:5070\n")
    app.run(debug=False, port=5070, host="127.0.0.1")
