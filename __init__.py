from __future__ import annotations

from typing import Any, Dict, Optional

from aqt import gui_hooks, mw
from aqt.qt import QAction, Qt
from aqt.utils import tooltip

from .service import compute_tag_ratios
from .store import load_cache, save_cache
from .ui.dialog import TagRatioDialog
from .ui.render import build_panel_html
from .ui.config_dialog import ConfigDialog

_DLG: Optional[TagRatioDialog] = None

try:
    from aqt.reviewer import Reviewer  # type: ignore
except Exception:
    Reviewer = None  # type: ignore


def _addon_id() -> str:
    """
    Anki の addonManager に渡す "addon id"（=フォルダ名）を安定して取る。
    取れなければ __name__ から推定。
    """
    try:
        am = mw.addonManager
        if hasattr(am, "addonFromModule"):
            return am.addonFromModule(__name__)
    except Exception:
        pass
    return __name__.split(".")[0]


def _cfg() -> Dict[str, Any]:
    try:
        return mw.addonManager.getConfig(_addon_id()) or {}
    except Exception:
        return {}


# ----------------------------
# Anki search helpers
# ----------------------------

def _anki_quote(s: str) -> str:
    # Anki検索用：スペース対応 + ダブルクォートエスケープ
    return '"' + str(s).replace('"', r'\"') + '"'


def _normalize_search_scope(scope: str) -> str:
    """
    目的:
      - deck 名にスペースがあっても壊れないようにクォートする
      - 子デッキも確実に含めたいので (deck:"X" OR deck:"X::*") に拡張する

    方針:
      - まず "単純な deck:..." の形だけを対象にする（複雑クエリは触らない）
      - deck:* はそのまま
      - deck:"..." はそのまま解析して、必要なら ::* を OR で追加
      - deck:Foo Bar のような壊れやすい形も救済する
    """
    s = (scope or "").strip()
    if not s:
        return "deck:*"

    # すでに複雑な検索（OR/AND/括弧/他フィールド等）なら触らない
    # ※必要ならこの判定は緩められる
    lowered = s.lower()
    complex_markers = (" or ", " and ", "(", ")", "tag:", "note:", "deck:\"")  # deck:"" は後で明示対応
    if any(m in lowered for m in complex_markers if m != "deck:\""):
        # deck:"..." の単純形だけは後で扱うので、ここでは一旦スルー
        pass

    # deck:* は OK
    if lowered == "deck:*":
        return "deck:*"

    # 単純に deck: から始まるものだけ処理
    if not lowered.startswith("deck:"):
        return s

    rest = s[5:].strip()
    if rest == "*":
        return "deck:*"

    # rest が "..." で囲まれているかを軽く判定
    name: str
    if len(rest) >= 2 and rest[0] == '"' and rest[-1] == '"':
        # deck:"My Deck"
        name = rest[1:-1].replace(r'\"', '"')
    else:
        # deck:My Deck など（壊れる元） → そのまま名前扱いで救済
        name = rest

    # 子デッキを確実に含める（親そのもの OR 親::*）
    # すでに ::* 指定が名前に含まれていたら、そのまま deck:"X::*" のみにする
    if name.endswith("::*"):
        return f'deck:{_anki_quote(name)}'

    return f'(deck:{_anki_quote(name)} or deck:{_anki_quote(name + "::*")})'


def _normalize_search_scopes_multiline(scope_text: str) -> str:
    """
    複数行入力を想定：
      - 1行 = 1つのスコープ
      - 空行は無視
      - 各行に _normalize_search_scope を適用
      - 最後に OR で結合
    """
    raw = (scope_text or "").strip()
    if not raw:
        return "deck:*"

    lines = [ln.strip() for ln in raw.splitlines()]
    parts = []
    for ln in lines:
        if not ln:
            continue
        parts.append(_normalize_search_scope(ln))

    if not parts:
        return "deck:*"
    if len(parts) == 1:
        return parts[0]

    return "(" + " or ".join(parts) + ")"



# --- context 判定（Main/DeckBrowser にだけ差し込みたい）---

try:
    from aqt.deckbrowser import DeckBrowser  # type: ignore
except Exception:
    DeckBrowser = None  # type: ignore

try:
    from aqt.mainpage import MainPage  # type: ignore
except Exception:
    MainPage = None  # type: ignore


def _is_main_context(context) -> bool:
    if context is None:
        return False
    try:
        if DeckBrowser is not None and isinstance(context, DeckBrowser):
            return True
    except Exception:
        pass
    try:
        if MainPage is not None and isinstance(context, MainPage):
            return True
    except Exception:
        pass
    # import 失敗時の保険
    return type(context).__name__ in ("DeckBrowser", "MainPage")


def _refresh_main() -> None:
    # DeckBrowser がいれば refresh、ダメなら reset
    try:
        if getattr(mw, "deckBrowser", None) is not None:
            mw.deckBrowser.refresh()
            return
    except Exception:
        pass
    try:
        mw.reset()
    except Exception:
        pass


def _on_dialog_destroyed() -> None:
    global _DLG
    _DLG = None


def _open_dialog() -> None:
    global _DLG
    if _DLG is not None:
        try:
            _DLG.raise_()
            _DLG.activateWindow()
            return
        except Exception:
            _DLG = None

    _DLG = TagRatioDialog(parent=mw)
    _DLG.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
    _DLG.destroyed.connect(lambda *_: _on_dialog_destroyed())
    _DLG.show()
    _DLG.raise_()
    _DLG.activateWindow()


def _update_now() -> None:
    cfg = _cfg()
    try:
        col = mw.col
        if col is None:
            tooltip("Tag Ratio: collection not ready")
            return

        raw_scope = str(cfg.get("search_scope", "deck:*"))
        scope = _normalize_search_scopes_multiline(raw_scope)

        res = compute_tag_ratios(
            col=col,
            search_scope=scope,
            tags=list(cfg.get("tags", [])),
            tag_mode=str(cfg.get("tag_mode", "OR")).upper(),
            min_cards=int(cfg.get("min_cards", 0)),
            max_rows=int(cfg.get("max_rows", 30)),
        )

        if not res:
            tooltip("Tag Ratio: no data")
            return

        save_cache(res)
        tooltip("Tag Ratio: updated")
        _refresh_main()

        if _DLG is not None:
            try:
                _DLG.reload_from_cache()
            except Exception:
                pass

    except Exception as e:
        tooltip(f"Tag Ratio: update failed ({type(e).__name__})")
        # 必要なら showInfo(str(e)) にしてもOK

def _on_reviewer_will_close(reviewer) -> None:
    cfg = _cfg()
    if not bool(cfg.get("auto_update_on_reviewer_close", False)):
        return
    # Reviewer closeはUIスレッドなので、同期_update_nowでOK
    _update_now()



# --- Main への差し込み：webview_will_set_content 方式 ---

def _on_webview_will_set_content(web_content, context) -> None:
    cfg = _cfg()
    if str(cfg.get("ui_target", "main")) != "main":
        return
    if not _is_main_context(context):
        return

    cache = load_cache()
    html = build_panel_html(cache, cfg)

    try:
        web_content.body += html
    except Exception:
        pass


# --- pycmd handler（Update/Open dialog）---

def _on_webview_did_receive_js_message(handled, message, context):
    try:
        if message == "tag_ratio_update":
            _update_now()
            return (True, None)
        if message == "tag_ratio_open":
            _open_dialog()
            return (True, None)
    except Exception:
        pass
    return handled


def _setup_menu() -> None:
    a = QAction("Tag Ratio: Update now", mw)
    a.triggered.connect(_update_now)  # type: ignore[attr-defined]
    mw.form.menuTools.addAction(a)

    b = QAction("Tag Ratio: Open dialog", mw)
    b.triggered.connect(_open_dialog)  # type: ignore[attr-defined]
    mw.form.menuTools.addAction(b)


def init() -> None:
    _setup_menu()

    # Add-ons → Config でカスタムGUIを開く
    try:
        mw.addonManager.setConfigAction(_addon_id(), lambda: ConfigDialog(parent=mw).exec())
    except Exception:
        try:
            mw.addonManager.setConfigAction(__name__.split(".")[0], lambda: ConfigDialog(parent=mw).exec())
        except Exception:
            pass

    gui_hooks.webview_will_set_content.append(_on_webview_will_set_content)
    gui_hooks.webview_did_receive_js_message.append(_on_webview_did_receive_js_message)

    # NEW: Auto update after study (Reviewer close)
    try:
        if hasattr(gui_hooks, "reviewer_will_close"):
            gui_hooks.reviewer_will_close.append(_on_reviewer_will_close)  # type: ignore[attr-defined]
    except Exception:
        pass


init()
