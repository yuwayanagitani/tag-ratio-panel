from __future__ import annotations

import json
import os
from typing import Any, Dict

from aqt import mw


def _user_files_dir() -> str:
    addon_dir = os.path.dirname(__file__)
    d = os.path.join(addon_dir, "user_files")
    os.makedirs(d, exist_ok=True)
    return d


def _cache_path() -> str:
    return os.path.join(_user_files_dir(), "tag_ratio_cache.json")


def load_cache() -> Dict[str, Any]:
    path = _cache_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(data: Dict[str, Any]) -> None:
    path = _cache_path()
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        # 最悪は無視（骨組みなので）
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
