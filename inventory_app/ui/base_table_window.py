from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout,
    QHeaderView, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ..utils.widgets import make_label, make_separator


class SimpleTableWindow(QWidget):
    """
    A reusable window for simple single-field tables (Contractors, Customers, Suppliers).
    Subclass and override: window_title, entity_label, get_all(), add_entity(), delete_entity()
    """
    window_title = "Table Manager"
    entity_label = "Name"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.window_title)
        self.resize(640, 500)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        title = QLabel(self.window_title)
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()

        self.btn_add = QPushButton("＋  Add")
        self.btn_add.setObjectName("primary")
        self.btn_add.setFixedWidth(100)
        self.btn_delete = QPushButton("✕  Delete")
        self.btn_delete.setObjectName("danger")
        self.btn_delete.setFixedWidth(100)
        hdr.addWidget(self.btn_add)
        hdr.addWidget(self.btn_delete)
        root.addLayout(hdr)
        root.addWidget(make_separator())

        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText(f"Search {self.entity_label.lower()}s...")
        self.search.textChanged.connect(self._filter)
        root.addWidget(self.search)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", self.entity_label])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(False)
        root.addWidget(self.table)

        self.status = QLabel("")
        self.status.setObjectName("subtitle")
        root.addWidget(self.status)

        self.btn_add.clicked.connect(self._add_dialog)
        self.btn_delete.clicked.connect(self._delete_selected)

    def refresh(self):
        self._all_data = self.get_all()
        self._display(self._all_data)
        self.status.setText(f"{len(self._all_data)} record(s)")

    def _display(self, rows):
        self.table.setRowCount(0)
        for row_data in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, val in enumerate(row_data):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r, c, item)

    def _filter(self, text):
        filtered = [row for row in self._all_data if text.lower() in str(row[1]).lower()]
        self._display(filtered)

    def _add_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Add {self.entity_label}")
        dlg.setMinimumWidth(360)
        layout = QFormLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        fields = self.get_form_fields()
        widgets = {}
        for key, label in fields:
            le = QLineEdit()
            layout.addRow(make_label(label), le)
            widgets[key] = le

        btns = QHBoxLayout()
        ok = QPushButton("Save")
        ok.setObjectName("primary")
        cancel = QPushButton("Cancel")
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(ok)
        layout.addRow(btns)

        ok.clicked.connect(lambda: self._save(dlg, widgets))
        cancel.clicked.connect(dlg.reject)
        dlg.exec()

    def _save(self, dlg, widgets):
        values = {k: w.text().strip() for k, w in widgets.items()}
        if not all(values.values()):
            QMessageBox.warning(self, "Validation", "All fields are required.")
            return
        try:
            self.add_entity(values)
            self.refresh()
            dlg.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select a row to delete.")
            return
        entity_id = self.table.item(row, 0).text()
        name = self.table.item(row, 1).text()
        r = QMessageBox.question(self, "Confirm", f"Delete '{name}'?")
        if r == QMessageBox.StandardButton.Yes:
            try:
                self.delete_entity(entity_id)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ── Override these ────────────────────────────────────────
    def get_all(self) -> list:
        """Return list of tuples: (id, name, ...)"""
        return []

    def get_form_fields(self) -> list:
        """Return list of (key, label) for the add form."""
        return [("name", self.entity_label)]

    def add_entity(self, values: dict):
        pass

    def delete_entity(self, entity_id):
        pass
