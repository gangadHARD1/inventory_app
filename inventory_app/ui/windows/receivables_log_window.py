from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QTabWidget, QLineEdit, QSplitter, QDialog, QDoubleSpinBox,
    QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from ...utils.widgets import make_label, make_separator
from ... import db

STATUS_COLORS = {
    "Ordered":       "#f59e0b",
    "In Inspection": "#38bdf8",
    "Approved":      "#4ade80",
}


class ReceivablesLogWindow(QWidget):
    """Shows all receivables with their items. Tab 2 shows rejections."""

    def __init__(self, current_user, parent=None):
        self.current_user = current_user
        super().__init__(parent)
        self.setWindowTitle("Receivables Log & Rejections")
        self.resize(1100, 660)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20); root.setSpacing(14)

        hdr = QHBoxLayout()
        title = QLabel("Receivables"); title.setObjectName("title")
        hdr.addWidget(title); hdr.addStretch()
        btn_refresh = QPushButton("↺  Refresh"); btn_refresh.setObjectName("primary")
        btn_refresh.clicked.connect(self.refresh)
        hdr.addWidget(btn_refresh)
        root.addLayout(hdr)
        root.addWidget(make_separator())

        tabs = QTabWidget()

        # ── Tab 1: All receivables ────────────────────────────────────────────
        tab_all = QWidget()
        ta = QVBoxLayout(tab_all); ta.setContentsMargins(0, 12, 0, 0); ta.setSpacing(8)

        self.search_all = QLineEdit(); self.search_all.setPlaceholderText("Search PO or supplier...")
        self.search_all.textChanged.connect(self._filter_all)
        ta.addWidget(self.search_all)

        self.table_all = QTableWidget(); self.table_all.setColumnCount(7)
        self.table_all.setHorizontalHeaderLabels([
            "ID", "PO", "Supplier", "Date", "Status", "Items", "Submitted By"
        ])
        self.table_all.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table_all.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_all.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_all.verticalHeader().setVisible(False)
        ta.addWidget(self.table_all)
        tabs.addTab(tab_all, "All Receivables")

        # ── Tab 2: Rejections ─────────────────────────────────────────────────
        tab_rej = QWidget()
        tr = QVBoxLayout(tab_rej); tr.setContentsMargins(0, 12, 0, 0); tr.setSpacing(8)

        rej_info = QLabel(
            "Receivables that have had failed items during inspection, "
            "excluding fully approved ones."
        )
        rej_info.setObjectName("subtitle"); rej_info.setWordWrap(True)
        tr.addWidget(rej_info)

        self.search_rej = QLineEdit(); self.search_rej.setPlaceholderText("Search PO...")
        self.search_rej.textChanged.connect(self._filter_rej)
        tr.addWidget(self.search_rej)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: list
        left = QWidget()
        ll = QVBoxLayout(left); ll.setContentsMargins(0, 0, 8, 0); ll.setSpacing(4)
        self.table_rej = QTableWidget(); self.table_rej.setColumnCount(4)
        self.table_rej.setHorizontalHeaderLabels(["ID", "PO", "Date", "Status"])
        self.table_rej.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_rej.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_rej.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_rej.verticalHeader().setVisible(False)
        self.table_rej.itemSelectionChanged.connect(self._on_rej_selected)
        ll.addWidget(self.table_rej)
        splitter.addWidget(left)

        # Right: item breakdown
        right = QWidget()
        rl = QVBoxLayout(right); rl.setContentsMargins(8, 0, 0, 0); rl.setSpacing(4)
        self.rej_detail_lbl = QLabel("Select a receivable")
        self.rej_detail_lbl.setObjectName("subtitle")
        rl.addWidget(self.rej_detail_lbl)
        self.table_rej_items = QTableWidget(); self.table_rej_items.setColumnCount(5)
        self.table_rej_items.setHorizontalHeaderLabels([
            "Item", "Grade", "Ordered", "Passed", "Failed"
        ])
        self.table_rej_items.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_rej_items.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_rej_items.verticalHeader().setVisible(False)
        rl.addWidget(self.table_rej_items)
        splitter.addWidget(right)
        splitter.setSizes([350, 650])
        tr.addWidget(splitter)
        tabs.addTab(tab_rej, "Rejections")

        root.addWidget(tabs)

    def refresh(self):
        with db.get_session() as s:
            recs = s.query(db.Receivable).order_by(db.Receivable.timestamp.desc()).all()
            self._all_data = []
            self._rej_data = []
            for rec in recs:
                po_name  = rec.purchase_order.name if rec.purchase_order else "—"
                sup_name = rec.supplier.name       if rec.supplier        else "—"
                date_str = rec.timestamp.strftime("%d %b %Y") if rec.timestamp else "—"
                items_summary = "; ".join(
                    f"{it.item_name}({it.grade or 'no grade'}) x{it.quantity}"
                    for it in rec.items
                )
                self._all_data.append({
                    "id": rec.id, "po": po_name, "supplier": sup_name,
                    "date": date_str, "status": rec.status,
                    "items": items_summary, "by": rec.submitted_by or "—"
                })
                # Rejections: has failures and NOT fully approved
                if rec.has_failures and rec.status != "Approved":
                    self._rej_data.append({
                        "id": rec.id, "po": po_name,
                        "date": date_str, "status": rec.status,
                    })

        self._display_all(self._all_data)
        self._display_rej(self._rej_data)
        self.table_rej_items.setRowCount(0)
        self.rej_detail_lbl.setText("Select a receivable")

    def _display_all(self, rows):
        self.table_all.setRowCount(0)
        for row in rows:
            r = self.table_all.rowCount(); self.table_all.insertRow(r)
            vals = [str(row["id"]), row["po"], row["supplier"],
                    row["date"], row["status"], row["items"], row["by"]]
            for c, val in enumerate(vals):
                cell = QTableWidgetItem(val)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if c == 4:
                    cell.setForeground(QColor(STATUS_COLORS.get(val, "#94a3b8")))
                self.table_all.setItem(r, c, cell)

    def _filter_all(self, text):
        self._display_all([r for r in self._all_data
                           if text.lower() in r["po"].lower()
                           or text.lower() in r["supplier"].lower()])

    def _display_rej(self, rows):
        self.table_rej.setRowCount(0)
        for row in rows:
            r = self.table_rej.rowCount(); self.table_rej.insertRow(r)
            for c, val in enumerate([str(row["id"]), row["po"], row["date"], row["status"]]):
                cell = QTableWidgetItem(val)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if c == 3:
                    cell.setForeground(QColor(STATUS_COLORS.get(val, "#94a3b8")))
                self.table_rej.setItem(r, c, cell)

    def _filter_rej(self, text):
        self._display_rej([r for r in self._rej_data if text.lower() in r["po"].lower()])

    def _on_rej_selected(self):
        row = self.table_rej.currentRow()
        if row < 0:
            self.table_rej_items.setRowCount(0); return
        rec_id = int(self.table_rej.item(row, 0).text())
        with db.get_session() as s:
            rec = s.get(db.Receivable, rec_id)
            if not rec: return
            po_name = rec.purchase_order.name if rec.purchase_order else "—"
            self.rej_detail_lbl.setText(f"PO: {po_name}  |  Status: {rec.status}")
            self.table_rej_items.setRowCount(0)
            for it in rec.items:
                if it.qty_failed > 0:
                    r = self.table_rej_items.rowCount()
                    self.table_rej_items.insertRow(r)
                    for c, val in enumerate([
                        it.item_name, it.grade or "—",
                        f"{it.quantity:.2f}", f"{it.qty_passed:.2f}", f"{it.qty_failed:.2f}"
                    ]):
                        cell = QTableWidgetItem(val)
                        cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                        if c == 4:  # failed qty in red
                            cell.setForeground(QColor("#f87171"))
                        self.table_rej_items.setItem(r, c, cell)