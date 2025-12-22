from __future__ import annotations

import time
from collections import Counter
from typing import Any


def _chunks(ids: list[int], n: int = 400) -> list[list[int]]:
    return [ids[i : i + n] for i in range(0, len(ids), n)]


def _like_escape(s: str) -> str:
    # SQLite LIKE の % _ \ をエスケープ
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def compute_tag_ratios(
    col,
    search_scope: str,
    tags: list[str],
    tag_mode: str = "OR",
    min_cards: int = 0,
    max_rows: int = 30,
) -> dict[str, Any]:
    """
    母集団: col.find_cards(search_scope)
    分母: cards.id in scope を did ごとに count
    分子: scope かつ notes.tags が指定タグ条件を満たす cards を did ごとに count
    """
    tags = [t.strip() for t in tags if t and t.strip()]
    tag_mode = (tag_mode or "OR").upper()
    if tag_mode not in ("OR", "AND"):
        tag_mode = "OR"

    cids: list[int] = list(col.find_cards(search_scope))
    updated_at = int(time.time())

    if not cids:
        return {
            "updated_at": updated_at,
            "search_scope": search_scope,
            "tags": tags,
            "tag_mode": tag_mode,
            "rows": [],
            "totals": {"num": 0, "den": 0, "pct": 0.0},
        }

    den = Counter()  # did -> count
    num = Counter()  # did -> count

    for chunk in _chunks(cids):
        qmarks = ",".join("?" for _ in chunk)

        # 分母
        for did, cnt in col.db.all(
            f"SELECT did, COUNT(*) FROM cards WHERE id IN ({qmarks}) GROUP BY did",
            *chunk,
        ):
            den[int(did)] += int(cnt)

        # 分子（タグ条件なしなら 0 のまま）
        if tags:
            conds = []
            params: list[Any] = []
            for t in tags:
                # tags はスペース区切りなので「前後にスペース」を付けて完全一致で探す
                conds.append("instr(' ' || n.tags || ' ', ' ' || ? || ' ') > 0")
                params.append(t)

            if tag_mode == "OR":
                tag_where = "(" + " OR ".join(conds) + ")"
            else:
                tag_where = "(" + " AND ".join(conds) + ")"

            for did, cnt in col.db.all(
                f"""
                SELECT c.did, COUNT(*)
                FROM cards c
                JOIN notes n ON n.id = c.nid
                WHERE c.id IN ({qmarks})
                  AND {tag_where}
                GROUP BY c.did
                """,
                *chunk,
                *params,
            ):
                num[int(did)] += int(cnt)

    rows = []
    total_den = 0
    total_num = 0

    for did, dcnt in den.items():
        if dcnt < min_cards:
            continue
        ncnt = int(num.get(did, 0))
        pct = (ncnt / dcnt * 100.0) if dcnt else 0.0

        # deck name
        try:
            deck_name = col.decks.name(did)
        except Exception:
            try:
                deck = col.decks.get(did)
                deck_name = deck.get("name", str(did))
            except Exception:
                deck_name = str(did)

        rows.append(
            {
                "did": did,
                "deck": deck_name,
                "num": ncnt,
                "den": int(dcnt),
                "pct": float(pct),
            }
        )

        total_den += int(dcnt)
        total_num += int(ncnt)

    rows.sort(key=lambda r: (-r["pct"], -r["den"], r["deck"].lower()))
    rows = rows[: max_rows if max_rows > 0 else len(rows)]

    total_pct = (total_num / total_den * 100.0) if total_den else 0.0

    return {
        "updated_at": updated_at,
        "search_scope": search_scope,
        "tags": tags,
        "tag_mode": tag_mode,
        "rows": rows,
        "totals": {"num": total_num, "den": total_den, "pct": float(total_pct)},
    }
