from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QDialog, QFormLayout, QDoubleSpinBox, QMessageBox,
    QSplitter, QGroupBox, QLineEdit
)
from PySide6.QtCore import Qt
from ...utils.widgets import make_label, make_separator, SearchableComboBox
from ... import db
from ...db import stock as inv_stock
from datetime import datetime


STATUS_COLORS = {
    "Ordered":       "#f59e0b",
    "In Inspection": "#38bdf8",
    "Approved":      "#4ade80",
}


class ChangeStatusWindow(QWidget):
    def __init__(self, current_user, parent=None):
        self.current_user = current_user
        super().__init__(parent)
        self.setWindowTitle("Change Receivable Status")
        self.resize(1000, 640)
        self._selected_receivable_id = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20); root.setSpacing(14)

        title = QLabel("Change Receivable Status"); title.setObjectName("title")
        root.addWidget(title)
        root.addWidget(make_separator())

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left: receivable list ─────────────────────────────────────────────
        left = QWidget()
        ll = QVBoxLayout(left); ll.setContentsMargins(0, 0, 8, 0); ll.setSpacing(8)
        ll.addWidget(make_label("Receivables (non-Approved)"))

        self.search = QLineEdit(); self.search.setPlaceholderText("Search PO...")
        self.search.textChanged.connect(self._filter)
        ll.addWidget(self.search)

        self.rec_table = QTableWidget(); self.rec_table.setColumnCount(4)
        self.rec_table.setHorizontalHeaderLabels(["ID", "PO", "Date", "Status"])
        self.rec_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.rec_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rec_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.rec_table.verticalHeader().setVisible(False)
        self.rec_table.itemSelectionChanged.connect(self._on_receivable_selected)
        ll.addWidget(self.rec_table)

        btn_refresh = QPushButton("↺  Refresh"); btn_refresh.clicked.connect(self.refresh)
        ll.addWidget(btn_refresh)
        splitter.addWidget(left)

        # ── Right: item details + inspection ─────────────────────────────────
        right = QWidget()
        rl = QVBoxLayout(right); rl.setContentsMargins(8, 0, 0, 0); rl.setSpacing(8)

        self.rec_info = QLabel("Select a receivable to inspect")
        self.rec_info.setObjectName("subtitle"); self.rec_info.setWordWrap(True)
        rl.addWidget(self.rec_info)

        self.items_table = QTableWidget(); self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Item", "Grade", "Ordered Qty", "Passed", "Failed", "Remaining"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.items_table.verticalHeader().setVisible(False)
        rl.addWidget(self.items_table)

        btn_row = QHBoxLayout()
        self.btn_inspect = QPushButton("🔍  Start / Update Inspection")
        self.btn_inspect.setObjectName("primary"); self.btn_inspect.setEnabled(False)
        self.btn_inspect.clicked.connect(self._open_inspection_dialog)
        btn_row.addWidget(self.btn_inspect); btn_row.addStretch()
        rl.addLayout(btn_row)

        splitter.addWidget(right)
        splitter.setSizes([380, 620])
        root.addWidget(splitter)

    def refresh(self):
        with db.get_session() as s:
            recs = (s.query(db.Receivable)
                    .filter(db.Receivable.status != "Approved")
                    .order_by(db.Receivable.timestamp.desc()).all())
            self._all_recs = []
            for r in recs:
                po_name = r.purchase_order.name if r.purchase_order else "—"
                self._all_recs.append({
                    "id": r.id, "po": po_name,
                    "date": r.timestamp.strftime("%d %b %Y") if r.timestamp else "—",
                    "status": r.status,
                })
        self._display_recs(self._all_recs)
        self._clear_right()

    def _display_recs(self, recs):
        self.rec_table.setRowCount(0)
        for rec in recs:
            r = self.rec_table.rowCount(); self.rec_table.insertRow(r)
            for c, val in enumerate([str(rec["id"]), rec["po"], rec["date"], rec["status"]]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if c == 3:
                    color = STATUS_COLORS.get(val, "#94a3b8")
                    item.setForeground(Qt.GlobalColor.white)
                    item.setBackground(Qt.GlobalColor.transparent)
                    item.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor(color))
                self.rec_table.setItem(r, c, item)

    def _filter(self, text):
        filtered = [r for r in self._all_recs if text.lower() in r["po"].lower()]
        self._display_recs(filtered)

    def _clear_right(self):
        self._selected_receivable_id = None
        self.rec_info.setText("Select a receivable to inspect")
        self.items_table.setRowCount(0)
        self.btn_inspect.setEnabled(False)

    def _on_receivable_selected(self):
        row = self.rec_table.currentRow()
        if row < 0: self._clear_right(); return
        rec_id = int(self.rec_table.item(row, 0).text())
        self._selected_receivable_id = rec_id
        self._load_receivable_detail(rec_id)
        self.btn_inspect.setEnabled(True)

    def _load_receivable_detail(self, rec_id):
        with db.get_session() as s:
            rec = s.get(db.Receivable, rec_id)
            if not rec: return
            po_name  = rec.purchase_order.name if rec.purchase_order else "—"
            sup_name = rec.supplier.name if rec.supplier else "—"
            self.rec_info.setText(
                f"PO: {po_name}  |  Supplier: {sup_name}  |  "
                f"Status: {rec.status}  |  Submitted by: {rec.submitted_by or '—'}  |  "
                f"Date: {rec.timestamp.strftime('%d %b %Y %H:%M') if rec.timestamp else '—'}"
            )
            self.items_table.setRowCount(0)
            for it in rec.items:
                r = self.items_table.rowCount(); self.items_table.insertRow(r)
                remaining = it.quantity - it.qty_passed - it.qty_failed
                for c, val in enumerate([
                    it.item_name, it.grade or "—",
                    f"{it.quantity:.2f}", f"{it.qty_passed:.2f}",
                    f"{it.qty_failed:.2f}", f"{max(0, remaining):.2f}"
                ]):
                    cell = QTableWidgetItem(val)
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    self.items_table.setItem(r, c, cell)

    def _open_inspection_dialog(self):
        if not self._selected_receivable_id: return
        dlg = InspectionDialog(self._selected_receivable_id, self.current_user, self)
        if dlg.exec():
            self.refresh()
            # Re-select the same receivable if still present
            for r in range(self.rec_table.rowCount()):
                if self.rec_table.item(r, 0) and \
                   int(self.rec_table.item(r, 0).text()) == self._selected_receivable_id:
                    self.rec_table.selectRow(r)
                    break


class InspectionDialog(QDialog):
    def __init__(self, receivable_id, current_user, parent=None):
        super().__init__(parent)
        self.receivable_id  = receivable_id
        self.current_user   = current_user
        self.setWindowTitle("Inspect Receivable")
        self.setMinimumWidth(640)
        self._row_widgets = []   # list of (item_id, pass_spin, fail_spin)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20); root.setSpacing(12)

        with db.get_session() as s:
            rec = s.get(db.Receivable, self.receivable_id)
            po_name = rec.purchase_order.name if rec.purchase_order else "—"
            items   = list(rec.items)

            root.addWidget(make_label(f"PO: {po_name}  |  Status: {rec.status}"))
            root.addWidget(make_separator())

            # Header
            hdr = QHBoxLayout()
            for lbl, stretch in [("Item", 3), ("Grade", 2), ("Ordered", 1), ("Pass Qty", 1), ("Fail Qty", 1)]:
                l = QLabel(lbl); l.setObjectName("section")
                hdr.addWidget(l, stretch)
            root.addLayout(hdr)

            self._row_widgets = []
            for it in items:
                already_done = it.qty_passed + it.qty_failed
                remaining    = it.quantity - already_done
                row_w = QHBoxLayout()

                lbl_name = QLabel(it.item_name); lbl_name.setWordWrap(True)
                lbl_grade = QLabel(it.grade or "—")
                lbl_ordered = QLabel(f"{it.quantity:.2f}")

                pass_spin = QDoubleSpinBox()
                pass_spin.setRange(0, max(0, remaining))
                pass_spin.setDecimals(2); pass_spin.setValue(0)

                fail_spin = QDoubleSpinBox()
                fail_spin.setRange(0, max(0, remaining))
                fail_spin.setDecimals(2); fail_spin.setValue(0)

                # Keep pass+fail <= remaining
                def make_validator(ps, fs, rem):
                    def _v():
                        if ps.value() + fs.value() > rem:
                            fs.setValue(max(0, rem - ps.value()))
                    return _v
                pass_spin.valueChanged.connect(make_validator(pass_spin, fail_spin, remaining))
                fail_spin.valueChanged.connect(make_validator(fail_spin, pass_spin, remaining))

                row_w.addWidget(lbl_name, 3); row_w.addWidget(lbl_grade, 2)
                row_w.addWidget(lbl_ordered, 1)
                row_w.addWidget(pass_spin, 1); row_w.addWidget(fail_spin, 1)
                root.addLayout(row_w)

                self._row_widgets.append((it.id, pass_spin, fail_spin))

        btns = QHBoxLayout()
        ok = QPushButton("Save Inspection"); ok.setObjectName("success")
        cancel = QPushButton("Cancel")
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(ok)
        root.addLayout(btns)

        ok.clicked.connect(self._save); cancel.clicked.connect(self.reject)

    def _save(self):
        with db.get_session() as s:
            rec = s.get(db.Receivable, self.receivable_id)
            any_pass = False; any_fail = False; fully_done = True

            for item_id, pass_spin, fail_spin in self._row_widgets:
                it = s.get(db.ReceivableItem, item_id)
                add_pass = pass_spin.value()
                add_fail = fail_spin.value()

                it.qty_passed += add_pass
                it.qty_failed += add_fail

                if add_pass > 0: any_pass = True
                if add_fail > 0: any_fail = True

                remaining = it.quantity - it.qty_passed - it.qty_failed
                if remaining > 0.001:
                    fully_done = False

                if add_pass > 0:
                    item = s.get(db.Item, it.item_code)
                    if item:
                        inv_stock.add_stock(
                            s, item, add_pass,
                            supplier_id=rec.supplier_id,
                            grade=it.grade,
                        )

            # Update status
            if any_fail: rec.has_failures = True
            if any_pass or any_fail:
                rec.status = "In Inspection"
            if fully_done and not any(
                (s.get(db.ReceivableItem, iid).quantity -
                 s.get(db.ReceivableItem, iid).qty_passed -
                 s.get(db.ReceivableItem, iid).qty_failed) > 0.001
                for iid, _, __ in self._row_widgets
            ):
                # All items fully accounted for
                rec.status = "Approved"

            s.commit()

        self.accept()