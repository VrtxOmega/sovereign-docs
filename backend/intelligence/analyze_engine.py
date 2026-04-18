"""
Sovereign Docs — Intelligence Engine
Ollama-powered document analysis and refinement.
"""
import json
import requests
from typing import Dict, Any

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_HEALTH = "http://localhost:11434/api/tags"


def check_ollama_health() -> bool:
    """Quick health check — returns True if Ollama daemon is reachable."""
    try:
        r = requests.get(OLLAMA_HEALTH, timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def analyze_document(content: str, model: str = "qwen3:8b") -> Dict[str, Any]:
    """
    Passes document content to Ollama for structured analysis.
    Returns a dictionary of analysis results.
    """
    if not check_ollama_health():
        return {
            "summary": "Ollama is not running. Start Ollama to enable AI analysis.",
            "findings": [],
            "risk_level": "OFFLINE",
            "risk_justification": "Local LLM daemon unreachable at localhost:11434",
            "action_items": ["Start Ollama: run 'ollama serve' in a terminal"]
        }

    prompt = f"""
You are VERITAS Intelligence. Analyze the following document and extract:
1. An Executive Summary (3 sentences max).
2. Key Findings (3-5 bullet points).
3. Risk Assessment (Low, Medium, High) with 1 sentence justification.
4. Action Items (if any).

Output strictly in valid JSON format matching this schema:
{{
  "summary": "...",
  "findings": ["...", "..."],
  "risk_level": "...",
  "risk_justification": "...",
  "action_items": ["..."]
}}

Document Content:
---
{content}
---
"""

    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "temperature": 0.1
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        result_text = data.get("response", "{}")

        try:
            analysis = json.loads(result_text)
            return analysis
        except json.JSONDecodeError:
            print(f"[Ollama] Failed to parse JSON response: {result_text[:200]}")
            return {
                "summary": result_text,
                "findings": [],
                "risk_level": "UNKNOWN",
                "risk_justification": "Failed to parse structured output.",
                "action_items": []
            }

    except requests.exceptions.Timeout:
        return {
            "summary": "Analysis timed out. The document may be too large for the selected model.",
            "findings": [],
            "risk_level": "TIMEOUT",
            "risk_justification": "Ollama request exceeded 120s timeout",
            "action_items": ["Try a smaller model or shorter document"]
        }
    except Exception as e:
        print(f"[Analyze_Engine] Ollama request failed: {e}")
        return {
            "summary": "Analysis unavailable. Local LLM may be offline.",
            "findings": [],
            "risk_level": "ERROR",
            "risk_justification": str(e),
            "action_items": []
        }


def format_analysis_markdown(analysis: Dict[str, Any], original_content: str) -> str:
    """Combines structured analysis into markdown format prepended to original content."""
    md = "## ⬡ VERITAS Intelligence Report\n\n"

    if "summary" in analysis:
        md += f"**Executive Summary:**\n{analysis['summary']}\n\n"

    if "risk_level" in analysis:
        md += f"**Risk Assessment:** {analysis['risk_level'].upper()} - {analysis.get('risk_justification', '')}\n\n"

    if analysis.get("findings"):
        md += "**Key Findings:**\n"
        for finding in analysis["findings"]:
            md += f"- {finding}\n"
        md += "\n"

    if analysis.get("action_items"):
        md += "**Action Items:**\n"
        for item in analysis["action_items"]:
            md += f"- [ ] {item}\n"
        md += "\n"

    md += "---\n\n## Original Document Source\n\n"
    md += original_content
    return md


def refine_document_text(content: str, mode: str, model: str = "qwen3:8b") -> str:
    """Passes text to Ollama for refinement based on the mode."""
    if not check_ollama_health():
        return f"ERROR: Ollama is not running. Start Ollama to enable AI refinement."

    prompts = {
        "concise": "Rewrite the following text to be more concise and direct. Keep all important meaning but remove fluff.",
        "formal": "Rewrite the following text to have a highly professional, formal, and authoritative tone suitable for enterprise stakeholders.",
        "summary": "Write a 3-sentence executive summary of the following text, and place it at the very beginning of the text, separated by a line break."
    }

    instruction = prompts.get(mode, prompts["concise"])

    prompt = f"{instruction}\n\nStrictly return only the rewritten markdown text. Do not add any conversational filler like 'Here is the rewritten text:'.\n\nText:\n---\n{content}\n---"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.3
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        refined = data.get("response", "").strip()
        # Strip <think> blocks that some models produce
        if "<think>" in refined:
            import re
            refined = re.sub(r"<think>.*?</think>", "", refined, flags=re.DOTALL).strip()
        return refined
    except requests.exceptions.Timeout:
        return f"ERROR: Refinement timed out. Try a smaller model."
    except Exception as e:
        print(f"[Analyze_Engine] Ollama refine request failed: {e}")
        return f"ERROR: Could not refine text -> {str(e)}"
