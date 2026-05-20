# purchase_orders_window.py  — drop this in ui/windows/
# Uses the same SimpleTableWindow pattern as contractors/suppliers etc.
# Wire it up in main_dashboard.py the same way.

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout,
    QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from ...utils.widgets import make_label, make_separator
from ...auth.auth import can as auth_can, is_superuser
from ... import db


class PurchaseOrdersWindow(QWidget):
    def __init__(self, current_user, parent=None):
        self.current_user = current_user
        super().__init__(parent)
        self.setWindowTitle("Purchase Orders")
        self.resize(640, 480)
        self._build_ui()
        self.refresh()

    def _can(self, action):
        return auth_can(self.current_user.category, "purchase_orders", action) \
               or is_superuser(self.current_user.category)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20); root.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("Purchase Orders"); title.setObjectName("title")
        hdr.addWidget(title); hdr.addStretch()
        if self._can("add"):
            self.btn_add = QPushButton("＋  Add"); self.btn_add.setObjectName("primary")
            hdr.addWidget(self.btn_add)
        else: self.btn_add = None
        if self._can("delete"):
            self.btn_del = QPushButton("✕  Delete"); self.btn_del.setObjectName("danger")
            hdr.addWidget(self.btn_del)
        else: self.btn_del = None
        root.addLayout(hdr)
        root.addWidget(make_separator())

        self.search = QLineEdit(); self.search.setPlaceholderText("Search POs...")
        self.search.textChanged.connect(self._filter)
        root.addWidget(self.search)

        self.table = QTableWidget(); self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", "PO Name / Number"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        self.status = QLabel(""); self.status.setObjectName("subtitle")
        root.addWidget(self.status)

        if self.btn_add: self.btn_add.clicked.connect(self._add_dialog)
        if self.btn_del: self.btn_del.clicked.connect(self._delete_selected)

    def refresh(self):
        with db.get_session() as s:
            pos = s.query(db.PurchaseOrder).order_by(db.PurchaseOrder.name).all()
            self._all_data = [(p.id, p.name) for p in pos]
        self._display(self._all_data)
        self.status.setText(f"{len(self._all_data)} record(s)")

    def _display(self, rows):
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount(); self.table.insertRow(r)
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r, c, item)

    def _filter(self, text):
        self._display([r for r in self._all_data if text.lower() in r[1].lower()])

    def _add_dialog(self):
        dlg = QDialog(self); dlg.setWindowTitle("Add Purchase Order"); dlg.setMinimumWidth(360)
        form = QFormLayout(dlg); form.setContentsMargins(20, 20, 20, 20); form.setSpacing(12)
        name_edit = QLineEdit(); name_edit.setPlaceholderText("e.g. PO-2024-001")
        form.addRow(make_label("PO Name / Number *"), name_edit)
        btns = QHBoxLayout()
        ok = QPushButton("Save"); ok.setObjectName("primary")
        cancel = QPushButton("Cancel")
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(ok)
        form.addRow(btns)

        def save():
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(dlg, "Validation", "PO name is required."); return
            with db.get_session() as s:
                s.add(db.PurchaseOrder(name=name)); s.commit()
            self.refresh(); dlg.accept()

        ok.clicked.connect(save); cancel.clicked.connect(dlg.reject); dlg.exec()

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0: return
        po_id = int(self.table.item(row, 0).text())
        name  = self.table.item(row, 1).text()
        if QMessageBox.question(self, "Confirm", f"Delete PO '{name}'?") == QMessageBox.StandardButton.Yes:
            with db.get_session() as s:
                obj = s.get(db.PurchaseOrder, po_id)
                if obj: s.delete(obj); s.commit()
            self.refresh()