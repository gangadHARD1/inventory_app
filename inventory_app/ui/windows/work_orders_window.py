from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout,
    QHeaderView, QMessageBox, QListWidget, QListWidgetItem,
    QGroupBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from ...utils.widgets import make_label, make_separator
from ... import db
from ...auth.auth import can as auth_can, is_superuser


class WorkOrdersWindow(QWidget):
    def __init__(self, current_user, parent=None):
        self.current_user = current_user
        super().__init__(parent)
        self.setWindowTitle("Work Orders")
        self.resize(800, 560)
        self._build_ui()
        self.refresh()

    def _can(self, action):
        return auth_can(self.current_user.category, 'work_orders', action) or is_superuser(self.current_user.category)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("Work Orders")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()
        self.btn_add = QPushButton("＋  Add")
        self.btn_add.setObjectName("primary")
        self.btn_edit = QPushButton("✎  Edit")
        self.btn_del = QPushButton("✕  Delete")
        self.btn_del.setObjectName("danger")
        hdr.addWidget(self.btn_add)
        hdr.addWidget(self.btn_edit)
        hdr.addWidget(self.btn_del)
        root.addLayout(hdr)
        root.addWidget(make_separator())

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search work orders...")
        self.search.textChanged.connect(self._filter)
        root.addWidget(self.search)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Work Order Name", "Contractors | Customers"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        self.status = QLabel("")
        self.status.setObjectName("subtitle")
        root.addWidget(self.status)

        self.btn_add.clicked.connect(self._add_dialog)
        self.btn_edit.clicked.connect(self._edit_dialog)
        self.btn_del.clicked.connect(self._delete_selected)

    def refresh(self):
        with db.get_session() as s:
            orders = s.query(db.WorkOrder).order_by(db.WorkOrder.name).all()
            self._all_data = []
            for wo in orders:
                contractors = ", ".join(c.name for c in wo.contractors)
                customers = ", ".join(c.name for c in wo.customers)
                summary = f"{contractors or '—'}  |  {customers or '—'}"
                self._all_data.append((wo.id, wo.name, summary))
        self._display(self._all_data)
        self.status.setText(f"{len(self._all_data)} record(s)")

    def _display(self, rows):
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r, c, item)

    def _filter(self, text):
        filtered = [r for r in self._all_data if text.lower() in r[1].lower()]
        self._display(filtered)

    def _work_order_dialog(self, edit_id=None):
        dlg = QDialog(self)
        dlg.setWindowTitle("Edit Work Order" if edit_id else "Add Work Order")
        dlg.setMinimumWidth(520)
        root = QVBoxLayout(dlg)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        name_edit = QLineEdit()
        root.addWidget(make_label("Work Order Name *"))
        root.addWidget(name_edit)

        # Contractors multi-select
        cont_group = QGroupBox("CONTRACTORS")
        cont_layout = QVBoxLayout(cont_group)
        cont_list = QListWidget()
        cont_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        cont_list.setMaximumHeight(140)
        with db.get_session() as s:
            all_contractors = s.query(db.Contractor).order_by(db.Contractor.name).all()
            for c in all_contractors:
                item = QListWidgetItem(c.name)
                item.setData(Qt.ItemDataRole.UserRole, c.id)
                cont_list.addItem(item)
        cont_layout.addWidget(cont_list)
        root.addWidget(cont_group)

        # Customers multi-select
        cust_group = QGroupBox("CUSTOMERS")
        cust_layout = QVBoxLayout(cust_group)
        cust_list = QListWidget()
        cust_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        cust_list.setMaximumHeight(140)
        with db.get_session() as s:
            all_customers = s.query(db.Customer).order_by(db.Customer.name).all()
            for c in all_customers:
                item = QListWidgetItem(c.name)
                item.setData(Qt.ItemDataRole.UserRole, c.id)
                cust_list.addItem(item)
        cust_layout.addWidget(cust_list)
        root.addWidget(cust_group)

        # Pre-fill
        if edit_id:
            with db.get_session() as s:
                wo = s.get(db.WorkOrder, edit_id)
                if wo:
                    name_edit.setText(wo.name)
                    cont_ids = {c.id for c in wo.contractors}
                    cust_ids = {c.id for c in wo.customers}
                    for i in range(cont_list.count()):
                        item = cont_list.item(i)
                        if item.data(Qt.ItemDataRole.UserRole) in cont_ids:
                            item.setSelected(True)
                    for i in range(cust_list.count()):
                        item = cust_list.item(i)
                        if item.data(Qt.ItemDataRole.UserRole) in cust_ids:
                            item.setSelected(True)

        btns = QHBoxLayout()
        ok = QPushButton("Save")
        ok.setObjectName("success")
        cancel = QPushButton("Cancel")
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(ok)
        root.addLayout(btns)

        def save():
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(dlg, "Validation", "Work order name required.")
                return
            selected_cont_ids = [
                cont_list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(cont_list.count())
                if cont_list.item(i).isSelected()
            ]
            selected_cust_ids = [
                cust_list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(cust_list.count())
                if cust_list.item(i).isSelected()
            ]
            with db.get_session() as s:
                if edit_id:
                    wo = s.get(db.WorkOrder, edit_id)
                    wo.name = name
                    wo.contractors = [s.get(db.Contractor, cid) for cid in selected_cont_ids]
                    wo.customers = [s.get(db.Customer, cid) for cid in selected_cust_ids]
                else:
                    wo = db.WorkOrder(name=name)
                    wo.contractors = [s.get(db.Contractor, cid) for cid in selected_cont_ids]
                    wo.customers = [s.get(db.Customer, cid) for cid in selected_cust_ids]
                    s.add(wo)
                s.commit()
            self.refresh()
            dlg.accept()

        ok.clicked.connect(save)
        cancel.clicked.connect(dlg.reject)
        dlg.exec()

    def _add_dialog(self):
        self._work_order_dialog()

    def _edit_dialog(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select a work order to edit.")
            return
        edit_id = int(self.table.item(row, 0).text())
        self._work_order_dialog(edit_id=edit_id)

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        entity_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        r = QMessageBox.question(self, "Confirm", f"Delete work order '{name}'?")
        if r == QMessageBox.StandardButton.Yes:
            with db.get_session() as s:
                obj = s.get(db.WorkOrder, entity_id)
                if obj:
                    s.delete(obj)
                    s.commit()
            self.refresh()