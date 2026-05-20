from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout,
    QHeaderView, QMessageBox, QComboBox,QListWidget, QAbstractItemView,QListWidgetItem
)
from PySide6.QtCore import Qt
from ...ui.base_table_window import SimpleTableWindow
from ...utils.widgets import make_label, make_separator
from ...auth.auth import can as auth_can, is_superuser
from ... import db


def _make_window(_title, _entity_label, _table_name, _model_cls):
    """Factory that returns a SimpleTableWindow subclass for a single-field table."""
    class Win(SimpleTableWindow):
        window_title  = _title
        entity_label  = _entity_label
        _tname        = _table_name
        _model        = _model_cls

        def __init__(self, current_user, parent=None):
            self.current_user = current_user
            super().__init__(parent)

        def _can(self, action):
            return auth_can(self.current_user.category, self._tname, action) or is_superuser(self.current_user.category)

        # Override button visibility after build
        def _post_init_permissions(self):
            if not self._can("add"):    self.btn_add.setVisible(False)
            if not self._can("delete"): self.btn_delete.setVisible(False)

        def get_all(self):
            with db.get_session() as s:
                return [(o.id, o.name) for o in s.query(self._model).order_by(self._model.name).all()]

        def add_entity(self, values):
            if not self._can("add"):
                raise PermissionError("No permission to add")
            with db.get_session() as s:
                s.add(self._model(name=values["name"]))
                s.commit()

        def delete_entity(self, entity_id):
            if not self._can("delete"):
                raise PermissionError("No permission to delete")
            with db.get_session() as s:
                obj = s.get(self._model, int(entity_id))
                if obj:
                    s.delete(obj); s.commit()

    Win.__name__ = f"{_title.replace(' ', '')}Window"
    return Win


ContractorsWindow   = _make_window("Contractors",            "Contractor Name",    "contractors",           db.Contractor)
CustomersWindow     = _make_window("Customers",              "Customer Name",      "customers",             db.Customer)
SuppliersWindow     = _make_window("Suppliers",              "Supplier Name",      "suppliers",             db.Supplier)
ItemGroupsWindow    = _make_window("Item Groups",            "Group Name",         "item_groups",           db.ItemGroup)
WOCategoriesWindow  = _make_window("Work Order Categories",  "Category Name",      "work_order_categories", db.WorkOrderCategory)
MeasurementUnitsWindow = _make_window("Measurement Units", "Unit Name", "measurement_units", db.MeasurementUnit)


# ── Item Classes ──────────────────────────────────────────────────────────────
class ItemClassesWindow(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("Item Classes")
        self.resize(700, 520)
        self._build_ui()
        self.refresh()

    def _can(self, action):
        return auth_can(self.current_user.category, "item_classes", action) or is_superuser(self.current_user.category)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("Item Classes")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()
        if self._can("add"):
            self.btn_add = QPushButton("＋  Add")
            self.btn_add.setObjectName("primary")
            self.btn_add.setFixedWidth(100)
            hdr.addWidget(self.btn_add)
        else:
            self.btn_add = None
        if self._can("delete"):
            self.btn_del = QPushButton("✕  Delete")
            self.btn_del.setObjectName("danger")
            self.btn_del.setFixedWidth(100)
            hdr.addWidget(self.btn_del)
        else:
            self.btn_del = None
        root.addLayout(hdr)
        root.addWidget(make_separator())

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search item classes...")
        self.search.textChanged.connect(self._filter)
        root.addWidget(self.search)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Item Class", "Item Group"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        self.status = QLabel(""); self.status.setObjectName("subtitle")
        root.addWidget(self.status)

        if self.btn_add:  self.btn_add.clicked.connect(self._add_dialog)
        if self.btn_del:  self.btn_del.clicked.connect(self._delete_selected)

    def refresh(self):
            with db.get_session() as s:
                classes = s.query(db.ItemClass).order_by(db.ItemClass.name).all()
                self._all_data = [
                    (ic.id, ic.name, ", ".join(g.name for g in ic.item_groups))
                    for ic in classes
                ]
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
        self._display([r for r in self._all_data if text.lower() in r[1].lower() or text.lower() in r[2].lower()])

    def _add_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Item Class")
        dlg.setMinimumWidth(400)
        layout = QFormLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        name_edit = QLineEdit()
        layout.addRow(make_label("Class Name"), name_edit)

        group_list = QListWidget()
        group_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        group_list.setMaximumHeight(160)

        with db.get_session() as s:
            groups = s.query(db.ItemGroup).order_by(db.ItemGroup.name).all()
            if not groups:
                QMessageBox.warning(self, "No Groups", "Please add Item Groups first.")
                return
            for g in groups:
                item = QListWidgetItem(g.name)
                item.setData(Qt.ItemDataRole.UserRole, g.id)
                group_list.addItem(item)

        layout.addRow(make_label("Item Groups (multi-select)"), group_list)

        btns = QHBoxLayout()
        ok = QPushButton("Save"); ok.setObjectName("primary")
        cancel = QPushButton("Cancel")
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(ok)
        layout.addRow(btns)

        def save():
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(dlg, "Validation", "Class name required.")
                return
            selected_ids = [
                group_list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(group_list.count())
                if group_list.item(i).isSelected()
            ]
            if not selected_ids:
                QMessageBox.warning(dlg, "Validation", "Select at least one Item Group.")
                return
            with db.get_session() as s:
                ic = db.ItemClass(name=name)
                ic.item_groups = [s.get(db.ItemGroup, gid) for gid in selected_ids]
                s.add(ic)
                s.commit()
            self.refresh()
            dlg.accept()

        ok.clicked.connect(save)
        cancel.clicked.connect(dlg.reject)
        dlg.exec()

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0: return
        entity_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        if QMessageBox.question(self, "Confirm", f"Delete '{name}'?") == QMessageBox.StandardButton.Yes:
            with db.get_session() as s:
                obj = s.get(db.ItemClass, entity_id)
                if obj: s.delete(obj); s.commit()
            self.refresh()