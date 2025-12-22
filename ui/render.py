from __future__ import annotations

import datetime
from html import escape
from typing import Any, Dict


def _fmt_ts(ts: int | None) -> str:
    if not ts:
        return "never"
    try:
        dt = datetime.datetime.fromtimestamp(int(ts))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "unknown"


def build_panel_html(cache: Dict[str, Any], cfg: Dict[str, Any]) -> str:
    tags = cache.get("tags") or cfg.get("tags") or []
    tag_mode = cache.get("tag_mode") or cfg.get("tag_mode") or "OR"
    scope = cache.get("search_scope") or cfg.get("search_scope") or "deck:*"
    updated_at = cache.get("updated_at")

    rows = cache.get("rows") or []
    totals = cache.get("totals") or {"num": 0, "den": 0, "pct": 0.0}

    tag_txt = ", ".join(str(t) for t in tags) if tags else "(no tags)"
    head = f"""
<div id="tag-ratio-panel" style="margin-top: 16px; padding: 12px; border: 1px solid #ddd; border-radius: 10px;">
  <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
    <div>
      <div style="font-weight:600;">Tag Ratio</div>
      <div style="font-size: 12px; opacity: 0.8;">
        scope: {escape(str(scope))} / tags({escape(str(tag_mode))}): {escape(tag_txt)} / updated: {escape(_fmt_ts(updated_at))}
      </div>
    </div>
    <div style="display:flex; gap:10px; font-size: 12px;">
      <a href="pycmd(tag_ratio_update)">Update</a>
      <a href="pycmd(tag_ratio_open)">Open dialog</a>
    </div>
  </div>
"""

    if not rows:
        body = """
  <div style="margin-top:10px; font-size:12px; opacity:0.8;">
    No cached data. Click Update.
  </div>
</div>
"""
        return head + body

    items = []
    for r in rows:
        deck = escape(str(r.get("deck", "")))
        num = int(r.get("num", 0))
        den = int(r.get("den", 0))
        pct = float(r.get("pct", 0.0))
        items.append(
            f"""
  <div style="display:flex; justify-content:space-between; gap:12px; padding:4px 0; border-top: 1px solid rgba(0,0,0,0.06);">
    <div style="flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{deck}</div>
    <div style="white-space:nowrap;">{num}/{den} ({pct:.1f}%)</div>
  </div>
"""
        )

    total_line = f"""
  <div style="margin-top:8px; font-size:12px; font-weight:600;">
    Total: {int(totals.get("num",0))}/{int(totals.get("den",0))} ({float(totals.get("pct",0.0)):.1f}%)
  </div>
</div>
"""
    return head + "".join(items) + total_line
