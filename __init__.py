from __future__ import annotations

from typing import Any, Dict, Optional

from aqt import gui_hooks, mw
from aqt.qt import QAction, Qt
from aqt.utils import tooltip

from .service import compute_tag_ratios
from .store import load_cache, save_cache
from .ui.dialog import TagRatioDialog
from .ui.render import build_panel_html

_DLG: Optional[TagRatioDialog] = None


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

    def op():
        col = mw.col
        if col is None:
            return None
        return compute_tag_ratios(
            col=col,
            search_scope=str(cfg.get("search_scope", "deck:*")),
            tags=list(cfg.get("tags", [])),
            tag_mode=str(cfg.get("tag_mode", "OR")).upper(),
            min_cards=int(cfg.get("min_cards", 0)),
            max_rows=int(cfg.get("max_rows", 30)),
        )

    def done(res):
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

    try:
        mw.taskman.run_in_background(op, done)  # type: ignore[attr-defined]
    except Exception:
        done(op())


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
    gui_hooks.webview_will_set_content.append(_on_webview_will_set_content)
    gui_hooks.webview_did_receive_js_message.append(_on_webview_did_receive_js_message)


init()
