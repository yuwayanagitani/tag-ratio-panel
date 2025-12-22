from __future__ import annotations

from aqt import mw
from aqt.qt import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from aqt.utils import tooltip

from ..store import load_cache
from ..service import compute_tag_ratios
from ..store import save_cache


class TagRatioDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tag Ratio (by deck)")
        self.setMinimumWidth(760)
        self.setMinimumHeight(420)

        self.info = QLabel("")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Deck", "Tagged", "Total", "%"])

        self.btn_update = QPushButton("Update")
        self.btn_close = QPushButton("Close")

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.btn_update)
        btns.addWidget(self.btn_close)

        lay = QVBoxLayout()
        lay.addWidget(self.info)
        lay.addWidget(self.table)
        lay.addLayout(btns)
        self.setLayout(lay)

        self.btn_close.clicked.connect(self.close)  # type: ignore[attr-defined]
        self.btn_update.clicked.connect(self.update_now)  # type: ignore[attr-defined]

        self.reload_from_cache()

    def reload_from_cache(self) -> None:
        cache = load_cache()
        rows = cache.get("rows") or []
        self.info.setText(
            f"scope={cache.get('search_scope','')} tags={cache.get('tags',[])} mode={cache.get('tag_mode','')} updated_at={cache.get('updated_at','')}"
        )
        self.table.setRowCount(0)

        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            deck = str(r.get("deck", ""))
            num = int(r.get("num", 0))
            den = int(r.get("den", 0))
            pct = float(r.get("pct", 0.0))

            self.table.setItem(row, 0, QTableWidgetItem(deck))
            self.table.setItem(row, 1, QTableWidgetItem(str(num)))
            self.table.setItem(row, 2, QTableWidgetItem(str(den)))
            self.table.setItem(row, 3, QTableWidgetItem(f"{pct:.1f}"))

        self.table.resizeColumnsToContents()

    def update_now(self) -> None:
        cfg = mw.addonManager.getConfig(__name__.split(".")[0]) or {}  # module->addon name の雑対策

        res = compute_tag_ratios(
            col=mw.col,
            search_scope=str(cfg.get("search_scope", "deck:*")),
            tags=list(cfg.get("tags", [])),
            tag_mode=str(cfg.get("tag_mode", "OR")).upper(),
            min_cards=int(cfg.get("min_cards", 0)),
            max_rows=int(cfg.get("max_rows", 30)),
        )
        save_cache(res)
        tooltip("Updated")
        self.reload_from_cache()
