from __future__ import annotations

import datetime
from html import escape
from typing import Any, Dict, List


def _fmt_ts(ts: int | None) -> str:
    if not ts:
        return "never"
    try:
        dt = datetime.datetime.fromtimestamp(int(ts))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "unknown"


def _default_pct_bands() -> List[Dict[str, Any]]:
    return [
        {"min": 0, "max": 40, "color": "#e53935"},
        {"min": 40, "max": 70, "color": "#fb8c00"},
        {"min": 70, "max": 90, "color": "#43a047"},
        {"min": 90, "max": 101, "color": "#1e88e5"},
    ]


def _pick_color(pct: float, cfg: Dict[str, Any]) -> str:
    bands = cfg.get("pct_bands")
    if not isinstance(bands, list) or not bands:
        bands = _default_pct_bands()

    try:
        p = float(pct)
    except Exception:
        p = 0.0

    for b in bands:
        try:
            mn = float(b.get("min", 0))
            mx = float(b.get("max", 101))
            color = str(b.get("color", "#999"))
        except Exception:
            continue
        if mn <= p < mx:
            return color

    return "#999"


def build_panel_html(cache: Dict[str, Any], cfg: Dict[str, Any]) -> str:
    tags = cache.get("tags") or cfg.get("tags") or []
    tag_mode = cache.get("tag_mode") or cfg.get("tag_mode") or "OR"
    scope = cache.get("search_scope") or cfg.get("search_scope") or "deck:*"
    updated_at = cache.get("updated_at")

    rows = cache.get("rows") or []
    totals = cache.get("totals") or {"num": 0, "den": 0, "pct": 0.0}

    tag_txt = ", ".join(str(t) for t in tags) if tags else "(no tags)"

    # 外枠：中央寄せ + inline-block でコンテンツ幅に追従
    # 画面を超えるときは max-width & overflow-x で横スクロール
    head = f"""
<div id="tag-ratio-wrap" style="text-align:center; margin-top: 16px;">
  <div id="tag-ratio-panel" style="
      display:inline-block;
      text-align:left;
      padding: 12px;
      border: 1px solid rgba(0,0,0,0.18);
      border-radius: 10px;
      max-width: 95vw;
      overflow-x: auto;
  ">
    <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:12px;">
      <div>
        <div style="font-weight:600;">Tag Ratio</div>
        <div style="font-size: 12px; opacity: 0.82; margin-top:2px;">
          scope: {escape(str(scope))}<br>
          tags({escape(str(tag_mode))}): {escape(tag_txt)}<br>
          updated: {escape(_fmt_ts(updated_at))}
        </div>
      </div>
    </div>
"""

    if not rows:
        body = """
    <div style="margin-top:10px; font-size:12px; opacity:0.8;">
      No cached data. Click Update.
    </div>
  </div>
</div>
"""
        return head + body

    # テーブル：width:auto で内容に追従
    table_head = """
    <div style="padding: 0 5px;">
      <table style="
          border-collapse: collapse;
          width: auto;
          margin-top: 10px;
          font-size: 13px;
      ">
        <tbody>
"""

    # Sort by deck name (case-insensitive, stable)
    def _deck_key(r: Dict[str, Any]) -> str:
        try:
            return str(r.get("deck", "")).casefold()
        except Exception:
            return ""

    rows = sorted(rows, key=_deck_key)


    items = []
    for r in rows:
        deck = escape(str(r.get("deck", "")))
        num = int(r.get("num", 0))
        den = int(r.get("den", 0))
        pct = float(r.get("pct", 0.0))
        color = _pick_color(pct, cfg)

        items.append(
            f"""
        <tr style="border-top: 1px solid rgba(0,0,0,0.06);">
          <td style="padding: 8px 16px 8px 16px; white-space: nowrap;">
            <span style="
                display:inline-block;
                width: 10px;
                height: 10px;
                border-radius: 999px;
                background: {escape(color)};
                margin-right: 8px;
                vertical-align: -1px;
            "></span>
            {deck}
          </td>
          <td style="padding: 8px 16px 8px 16px; white-space: nowrap; text-align:right;">
            {num}/{den} ({pct:.1f}%)
          </td>
        </tr>
"""
        )

    table_tail = """
        </tbody>
      </table>
    </div>
"""
    total_line = f"""
    <div style="margin-top:8px; font-size:12px; font-weight:600; white-space:nowrap;">
      Total: {int(totals.get("num",0))}/{int(totals.get("den",0))} ({float(totals.get("pct",0.0)):.1f}%)
    </div>
  </div>
</div>
"""
    return head + table_head + "".join(items) + table_tail + total_line
