from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QCheckBox, QFrame, QScrollArea,
    QMessageBox
)
from PySide6.QtCore import Qt
from ...utils.widgets import make_label, make_separator
from ... import db

ALL_TABLES = [
    "items", "item_groups", "item_classes", "measurement_units",
    "contractors", "customers", "suppliers",
    "work_orders", "work_order_categories",
    "employees", "issues",
]
ACTIONS     = ["can_view", "can_add", "can_edit", "can_delete", "can_create_employee", "can_adhoc_issue"]
ACT_LABELS  = ["View",     "Add",    "Edit",    "Delete",    "Create Emp",           "Ad-hoc Issue"]


class RolesWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Role Permissions")
        self.resize(920, 620)
        self._category = None
        self._checkboxes = {}
        self._build_ui()
        self._load_categories()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        hdr = QHBoxLayout()
        title = QLabel("Role Permissions")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()
        root.addLayout(hdr)
        root.addWidget(make_separator())

        cat_row = QHBoxLayout()
        cat_row.addWidget(make_label("Category:"))
        self.cat_combo = QComboBox()
        self.cat_combo.setMinimumWidth(200)
        self.cat_combo.currentTextChanged.connect(self._on_category_change)
        cat_row.addWidget(self.cat_combo)
        cat_row.addSpacing(16)
        cat_row.addWidget(make_label("New category:"))
        self.new_cat_edit = QLineEdit()
        self.new_cat_edit.setPlaceholderText("e.g. Supervisor")
        self.new_cat_edit.setFixedWidth(160)
        cat_row.addWidget(self.new_cat_edit)
        btn_add_cat = QPushButton("Add")
        btn_add_cat.setObjectName("primary")
        btn_add_cat.clicked.connect(self._add_category)
        cat_row.addWidget(btn_add_cat)
        cat_row.addStretch()
        root.addLayout(cat_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        grid_widget = QWidget()
        grid_layout = QVBoxLayout(grid_widget)
        grid_layout.setSpacing(0)

        # Header
        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("Table"), 3)
        for lbl in ACT_LABELS:
            l = QLabel(lbl)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setStyleSheet("color:#38bdf8; font-size:11px; font-weight:600; letter-spacing:1px;")
            header_row.addWidget(l, 1)
        grid_layout.addLayout(header_row)
        grid_layout.addWidget(make_separator())

        self._checkboxes = {}
        for i, table in enumerate(ALL_TABLES):
            row_frame = QFrame()
            row_frame.setStyleSheet("background:#1a1f2e;" if i % 2 == 0 else "background:#131720;")
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(8, 6, 8, 6)
            lbl = QLabel(table.replace("_", " ").title())
            lbl.setStyleSheet("color:#cbd5e1; font-size:12px;")
            row_layout.addWidget(lbl, 3)
            for action in ACTIONS:
                cb = QCheckBox()
                cb.setStyleSheet("QCheckBox::indicator { width:16px; height:16px; }")
                container = QWidget()
                cl = QHBoxLayout(container)
                cl.setContentsMargins(0, 0, 0, 0)
                cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cl.addWidget(cb)
                row_layout.addWidget(container, 1)
                self._checkboxes[(table, action)] = cb
            grid_layout.addWidget(row_frame)

        scroll.setWidget(grid_widget)
        root.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save = QPushButton("💾  Save Permissions")
        btn_save.setObjectName("success")
        btn_save.setFixedWidth(200)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    def _load_categories(self):
        self.cat_combo.blockSignals(True)
        self.cat_combo.clear()
        with db.get_session() as s:
            cats = s.query(db.Employee.category).distinct().filter(
                db.Employee.category.isnot(None)
            ).all()
            categories = sorted({c[0] for c in cats if c[0].lower() not in ("admin", "store manager")})
        for c in categories:
            self.cat_combo.addItem(c)
        self.cat_combo.blockSignals(False)
        if self.cat_combo.count() > 0:
            self._on_category_change(self.cat_combo.currentText())
        else:
            self._clear_checkboxes()

    def _add_category(self):
        name = self.new_cat_edit.text().strip()
        if not name:
            return
        if name.lower() in ("admin", "store manager"):
            QMessageBox.warning(self, "Reserved", f"'{name}' is a superuser category.")
            return
        if self.cat_combo.findText(name) == -1:
            self.cat_combo.addItem(name)
        self.cat_combo.setCurrentText(name)
        self.new_cat_edit.clear()

    def _on_category_change(self, category):
        self._category = category
        self._clear_checkboxes()
        if not category:
            return
        with db.get_session() as s:
            perms = s.query(db.RolePermission).filter_by(category=category).all()
            perm_map = {p.table_name: p for p in perms}
        for table in ALL_TABLES:
            p = perm_map.get(table)
            for action in ACTIONS:
                self._checkboxes[(table, action)].setChecked(getattr(p, action, False) if p else False)

    def _clear_checkboxes(self):
        for cb in self._checkboxes.values():
            cb.setChecked(False)

    def _save(self):
        if not self._category:
            QMessageBox.warning(self, "No Category", "Select or add a category first.")
            return
        with db.get_session() as s:
            for table in ALL_TABLES:
                existing = s.query(db.RolePermission).filter_by(
                    category=self._category, table_name=table
                ).first()
                if not existing:
                    existing = db.RolePermission(category=self._category, table_name=table)
                    s.add(existing)
                for action in ACTIONS:
                    setattr(existing, action, self._checkboxes[(table, action)].isChecked())
            s.commit()
        QMessageBox.information(self, "Saved", f"Permissions saved for '{self._category}'.")