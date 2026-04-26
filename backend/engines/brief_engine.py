"""
SOVEREIGN DOCS — Brief Engine
==============================
Generates Daily, Weekly, and Custom Intelligence Briefs from the Moltbook /
VERITAS Vault sources. Designed to fail gracefully when external dependencies
are missing — returns a structured "offline" payload instead of crashing.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional


# ── PATH BOOTSTRAP ────────────────────────────────────────────────
# These are the only locations the Vault / Moltbook bridges can live in.
# We push them onto sys.path on entry and pop them on exit so we don't
# pollute the global module namespace for other consumers of this engine.
_BRIDGE_PATHS = [
    "C:\\Veritas_Lab",
    "C:\\Veritas_Lab\\gravity-omega-v2\\backend\\modules",
]


def _push_paths() -> None:
    for p in _BRIDGE_PATHS:
        if p not in sys.path:
            sys.path.insert(0, p)


def _pop_paths() -> None:
    for p in _BRIDGE_PATHS:
        try:
            sys.path.remove(p)
        except ValueError:
            pass


def _gather_posts(since: datetime, until: Optional[datetime] = None) -> tuple[list, str]:
    """
    Pull artifacts from the Moltbook bridge.

    Returns (posts, status):
      • posts is a list of dicts with at least {title, created_at, content}
      • status is one of: "ok", "offline" (bridge missing), "error: <msg>"
    """
    _push_paths()
    try:
        try:
            from morning_brief import gather_moltbook_activity  # type: ignore
        except ImportError:
            return [], "offline"

        try:
            posts = gather_moltbook_activity(since)
        except Exception as e:
            return [], f"error: {e}"

        if until is not None:
            posts = [p for p in posts if _post_is_before(p, until)]

        return posts, "ok"
    finally:
        _pop_paths()


def _post_is_before(post: dict, cutoff: datetime) -> bool:
    """Return True if the post's created_at falls strictly before cutoff."""
    raw = post.get("created_at")
    if not raw:
        return True
    try:
        # Try ISO first; fall back to a permissive parse.
        ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00").rstrip("+00:00"))
    except ValueError:
        try:
            ts = datetime.strptime(str(raw)[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return True
    return ts < cutoff


# ── RENDERERS ──────────────────────────────────────────────────────
def _render_offline_brief(title: str, window_label: str) -> str:
    return "\n".join([
        f"# {title}",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> Window: {window_label}",
        "",
        "## Status",
        "- **Vault Bridge**: OFFLINE",
        "- **Reason**: `morning_brief.gather_moltbook_activity` not importable.",
        "",
        "## What this means",
        "The Moltbook integration could not be loaded. This is normal if you're",
        "running Sovereign Docs without the full Gravity-Omega stack.",
        "",
        "Sovereign Docs will continue to work for everything else (Create,",
        "Extract, Forge, Analyze, Library). The Brief tab will start producing",
        "real intelligence rollups once `gravity-omega-v2/backend/modules/morning_brief.py`",
        "is available on disk.",
    ])


def _render_brief(title: str, window_label: str, posts: list,
                  since: datetime, until: datetime) -> str:
    md = [
        f"# {title}",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> Window: {window_label}",
        "",
        "## System Telemetry",
        "- **Status**: ACTIVE",
        f"- **From**: {since.strftime('%Y-%m-%d %H:%M')}",
        f"- **To**:   {until.strftime('%Y-%m-%d %H:%M')}",
        f"- **Signals Caught**: {len(posts)}",
        "",
        "## Autonomous Artifacts",
    ]

    if not posts:
        md.append("\n*No significant artifacts recorded in the observation window.*\n")
    else:
        for post in posts:
            heading = post.get("title") or "Untitled Signal"
            created = post.get("created_at") or ""
            content = (post.get("content") or "").strip()
            md.append(f"### {heading}")
            if created:
                md.append(f"*{created}*")
            if content:
                md.append("")
                md.append(content)
            md.append("")
            md.append("---")
            md.append("")

    md.append("*End of Brief*")
    return "\n".join(md)


# ── PUBLIC API ─────────────────────────────────────────────────────
def generate_brief(brief_type: str = "daily",
                   start: Optional[str] = None,
                   end: Optional[str] = None) -> dict:
    """
    Unified entrypoint for all brief types.

    Args:
        brief_type: 'daily' (last 48h), 'weekly' (last 7d), or 'custom'
        start: ISO date string for custom briefs
        end:   ISO date string for custom briefs

    Returns:
        {
          "success": bool,
          "type": str,
          "content": str,        # markdown body
          "vault_status": str,   # 'ok' | 'offline' | 'error: ...'
          "post_count": int,
          "window_label": str,
        }
    """
    now = datetime.now()

    if brief_type == "daily":
        since = now - timedelta(hours=48)
        until = now
        title = "Daily Intelligence Rollup"
        window_label = "Past 48 hours"

    elif brief_type == "weekly":
        since = now - timedelta(days=7)
        until = now
        title = "Weekly Intelligence Rollup"
        window_label = "Past 7 days"

    elif brief_type == "custom":
        try:
            since = _parse_date(start) if start else (now - timedelta(days=7))
            until = _parse_date(end) if end else now
        except ValueError as e:
            return {
                "success": False,
                "type": brief_type,
                "content": "",
                "vault_status": f"error: bad date — {e}",
                "post_count": 0,
                "window_label": "",
            }
        if since > until:
            since, until = until, since
        title = "Custom Intelligence Brief"
        window_label = f"{since.strftime('%Y-%m-%d')} \u2192 {until.strftime('%Y-%m-%d')}"

    else:
        return {
            "success": False,
            "type": brief_type,
            "content": "",
            "vault_status": f"error: unknown brief type '{brief_type}'",
            "post_count": 0,
            "window_label": "",
        }

    posts, status = _gather_posts(since, until)

    if status == "offline":
        body = _render_offline_brief(title, window_label)
        return {
            "success": True,
            "type": brief_type,
            "content": body,
            "vault_status": "offline",
            "post_count": 0,
            "window_label": window_label,
        }

    if status.startswith("error"):
        body = "\n".join([
            f"# {title} — Error",
            f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Vault bridge raised an unexpected error while gathering posts:",
            "",
            "```text",
            status,
            "```",
        ])
        return {
            "success": False,
            "type": brief_type,
            "content": body,
            "vault_status": status,
            "post_count": 0,
            "window_label": window_label,
        }

    body = _render_brief(title, window_label, posts, since, until)
    return {
        "success": True,
        "type": brief_type,
        "content": body,
        "vault_status": "ok",
        "post_count": len(posts),
        "window_label": window_label,
    }


def _parse_date(s: str) -> datetime:
    """Accept YYYY-MM-DD or full ISO; raise ValueError on bad input."""
    s = (s or "").strip()
    if not s:
        raise ValueError("empty date")
    # Try full ISO first (datetime-local sends 'YYYY-MM-DDTHH:MM').
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        pass
    return datetime.strptime(s, "%Y-%m-%d")


# ── BACKWARDS-COMPAT SHIM ──────────────────────────────────────────
def generate_daily_brief() -> str:
    """Old API — still used by some callers. Returns just the markdown body."""
    return generate_brief("daily")["content"]
