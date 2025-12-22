from __future__ import annotations

from typing import Any, Dict, List

from aqt import mw
from aqt.qt import (
    QAbstractItemView,
    QColor,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from aqt.utils import tooltip


def _addon_name_from_module() -> str:
    # setConfigAction / getConfig / writeConfig 用のキー
    # 基本はフォルダ名 (= top module)
    return __name__.split(".")[0]


def _load_cfg() -> Dict[str, Any]:
    return mw.addonManager.getConfig(_addon_name_from_module()) or {}


def _save_cfg(cfg: Dict[str, Any]) -> None:
    mw.addonManager.writeConfig(_addon_name_from_module(), cfg)


class ConfigDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tag Ratio Settings")
        self.setMinimumWidth(720)

        cfg = _load_cfg()

        root = QVBoxLayout(self)

        # --- General ---
        general = QGroupBox("General")
        g = QGridLayout(general)

        self.ui_target = QComboBox()
        self.ui_target.addItems(["main", "none"])
        self.ui_target.setCurrentText(str(cfg.get("ui_target", "main")))

        self.tag_mode = QComboBox()
        self.tag_mode.addItems(["OR", "AND"])
        self.tag_mode.setCurrentText(str(cfg.get("tag_mode", "OR")).upper())

        self.min_cards = QSpinBox()
        self.min_cards.setMinimum(0)
        self.min_cards.setMaximum(10_000_000)
        self.min_cards.setValue(int(cfg.get("min_cards", 0)))

        self.max_rows = QSpinBox()
        self.max_rows.setMinimum(1)
        self.max_rows.setMaximum(10_000)
        self.max_rows.setValue(int(cfg.get("max_rows", 30)))

        g.addWidget(QLabel("UI target"), 0, 0)
        g.addWidget(self.ui_target, 0, 1)
        g.addWidget(QLabel("Tag mode"), 1, 0)
        g.addWidget(self.tag_mode, 1, 1)
        g.addWidget(QLabel("Min cards"), 2, 0)
        g.addWidget(self.min_cards, 2, 1)
        g.addWidget(QLabel("Max rows"), 3, 0)
        g.addWidget(self.max_rows, 3, 1)

        root.addWidget(general)

        # --- Scope ---
        scope = QGroupBox("Scope")
        s = QGridLayout(scope)

        self.search_scope = QPlainTextEdit()
        self.search_scope.setPlaceholderText(
            'One scope per line.\n'
            'Examples:\n'
            'deck:*\n'
            'deck:"My Deck"\n'
            'deck:Parent\n'
        )
        self.search_scope.setPlainText(str(cfg.get("search_scope", "deck:*")))
        self.search_scope.setMinimumHeight(90)

        scope_help = QLabel(
            'Enter <b>one scope per line</b>. You do <b>not</b> need to write <code>OR</code>.<br/>'
            'Each line is normalized and then combined with OR automatically.<br/>'
            'Examples:<br/>'
            '• <code>deck:*</code> = all decks<br/>'
            '• <code>deck:"My Deck"</code> = deck name with spaces (quotes required)<br/>'
            '• <code>deck:"Parent"</code> = parent deck (subdecks are included automatically by normalization)'
        )
        scope_help.setWordWrap(True)

        s.addWidget(QLabel("Search scope"), 0, 0)
        s.addWidget(self.search_scope, 0, 1)
        root.addWidget(scope)

        # --- Tags ---
        tags_box = QGroupBox("Tags")
        t = QGridLayout(tags_box)

        self.tags_line = QLineEdit()
        self.tags_line.setPlaceholderText('Comma-separated. e.g. needs_coverage_key,foo,bar')
        tags = cfg.get("tags", [])
        if isinstance(tags, list):
            self.tags_line.setText(",".join(str(x) for x in tags))
        else:
            self.tags_line.setText(str(tags))

        tags_help = QLabel(
            'Enter <b>tag names</b> as a <b>comma-separated</b> list.<br/>'
            'Example: <code>anatomy,physiology,needs_coverage_key</code><br/>'
            'Do not write <code>tag:</code> here.<br/>'
            '<b>Tag mode</b> controls how multiple tags are combined: OR (any) / AND (all).'
        )
        tags_help.setWordWrap(True)

        t.addWidget(QLabel("Tags"), 0, 0)
        t.addWidget(self.tags_line, 0, 1)
        root.addWidget(tags_box)

        # --- Percent bands ---
        bands_box = QGroupBox("Percent bands (left colored dot)")
        vb = QVBoxLayout(bands_box)

        self.bands_table = QTableWidget()
        self.bands_table.setColumnCount(3)
        self.bands_table.setHorizontalHeaderLabels(["min", "max", "color"])
        self.bands_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bands_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.bands_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)

        vb.addWidget(self.bands_table)

        btns = QHBoxLayout()
        self.add_band_btn = QPushButton("Add")
        self.del_band_btn = QPushButton("Remove")
        self.pick_color_btn = QPushButton("Pick color…")
        btns.addWidget(self.add_band_btn)
        btns.addWidget(self.del_band_btn)
        btns.addStretch(1)
        btns.addWidget(self.pick_color_btn)
        vb.addLayout(btns)

        root.addWidget(bands_box)

        self.add_band_btn.clicked.connect(self._add_band)
        self.del_band_btn.clicked.connect(self._del_band)
        self.pick_color_btn.clicked.connect(self._pick_color)

        self._load_bands(cfg.get("pct_bands"))

        # --- OK / Cancel ---
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        box.accepted.connect(self._on_ok)
        box.rejected.connect(self.reject)
        root.addWidget(box)

    def _load_bands(self, pct_bands: Any) -> None:
        default = [
            {"min": 0, "max": 40, "color": "#e53935"},
            {"min": 40, "max": 70, "color": "#fb8c00"},
            {"min": 70, "max": 90, "color": "#43a047"},
            {"min": 90, "max": 101, "color": "#1e88e5"},
        ]
        bands = pct_bands if isinstance(pct_bands, list) else default

        self.bands_table.setRowCount(0)
        for b in bands:
            self._append_band_row(
                int(b.get("min", 0)),
                int(b.get("max", 0)),
                str(b.get("color", "#000000")),
            )

        self.bands_table.resizeColumnsToContents()

    def _append_band_row(self, mn: int, mx: int, color: str) -> None:
        r = self.bands_table.rowCount()
        self.bands_table.insertRow(r)

        self.bands_table.setItem(r, 0, QTableWidgetItem(str(mn)))
        self.bands_table.setItem(r, 1, QTableWidgetItem(str(mx)))
        self.bands_table.setItem(r, 2, QTableWidgetItem(color))

        self._apply_color_to_row(r, color)

    def _apply_color_to_row(self, row: int, color_hex: str) -> None:
        col_item = self.bands_table.item(row, 2)
        if not col_item:
            return
        qcol = QColor(color_hex)
        if not qcol.isValid():
            return
        col_item.setBackground(qcol)

    def _add_band(self) -> None:
        self._append_band_row(0, 0, "#000000")
        self.bands_table.resizeColumnsToContents()

    def _del_band(self) -> None:
        row = self.bands_table.currentRow()
        if row < 0:
            return
        self.bands_table.removeRow(row)

    def _pick_color(self) -> None:
        row = self.bands_table.currentRow()
        if row < 0:
            tooltip("Select a band row first.")
            return
        cur = self.bands_table.item(row, 2).text() if self.bands_table.item(row, 2) else "#000000"
        initial = QColor(cur)
        col = QColorDialog.getColor(initial, self, "Pick color")
        if not col.isValid():
            return
        hex_ = col.name()
        if self.bands_table.item(row, 2) is None:
            self.bands_table.setItem(row, 2, QTableWidgetItem(hex_))
        else:
            self.bands_table.item(row, 2).setText(hex_)
        self._apply_color_to_row(row, hex_)

    def _collect_bands(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for r in range(self.bands_table.rowCount()):
            mn_txt = self.bands_table.item(r, 0).text() if self.bands_table.item(r, 0) else "0"
            mx_txt = self.bands_table.item(r, 1).text() if self.bands_table.item(r, 1) else "0"
            col_txt = self.bands_table.item(r, 2).text() if self.bands_table.item(r, 2) else "#000000"

            try:
                mn = int(mn_txt)
                mx = int(mx_txt)
            except Exception:
                raise ValueError(f"Row {r+1}: min/max must be integers.")

            if mx <= mn:
                raise ValueError(f"Row {r+1}: max must be > min.")

            qcol = QColor(col_txt)
            if not qcol.isValid():
                raise ValueError(f"Row {r+1}: invalid color '{col_txt}'.")

            out.append({"min": mn, "max": mx, "color": col_txt})

        # min順にソート（見た目/安定性）
        out.sort(key=lambda x: int(x.get("min", 0)))
        return out

    def _on_ok(self) -> None:
        try:
            cfg = _load_cfg()

            cfg["ui_target"] = self.ui_target.currentText()
            cfg["search_scope"] = self.search_scope.toPlainText().strip() or "deck:*"
            cfg["tag_mode"] = self.tag_mode.currentText().upper()
            cfg["min_cards"] = int(self.min_cards.value())
            cfg["max_rows"] = int(self.max_rows.value())

            tags_raw = self.tags_line.text().strip()
            if tags_raw:
                tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
            else:
                tags = []
            cfg["tags"] = tags

            cfg["pct_bands"] = self._collect_bands()

            _save_cfg(cfg)
            tooltip("Saved.")
            self.accept()
        except Exception as e:
            tooltip(f"Config error: {e}")
            return
