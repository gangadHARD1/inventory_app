from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout, QDateEdit,
    QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from ...utils.widgets import make_label, make_separator
from ... import db
from ...auth.auth import can as auth_can, is_superuser, hash_password
from datetime import date


class EmployeesWindow(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("Employees")
        self.resize(860, 540)
        self._build_ui()
        self.refresh()

    def _can(self, action):
        return auth_can(self.current_user.category, "employees", action)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("Employees")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()

        can_create = is_superuser(self.current_user.category) or self._can("create_employee")
        if can_create:
            self.btn_add = QPushButton("＋  Add Employee")
            self.btn_add.setObjectName("primary")
            hdr.addWidget(self.btn_add)
        else:
            self.btn_add = None

        if self._can("edit"):
            self.btn_edit = QPushButton("✎  Edit")
            hdr.addWidget(self.btn_edit)
        else:
            self.btn_edit = None

        if self._can("delete"):
            self.btn_del = QPushButton("✕  Delete")
            self.btn_del.setObjectName("danger")
            hdr.addWidget(self.btn_del)
        else:
            self.btn_del = None

        if self._can("edit") or is_superuser(self.current_user.category):
            self.btn_reset = QPushButton("🔑  Reset Password")
            hdr.addWidget(self.btn_reset)
        else:
            self.btn_reset = None

        root.addLayout(hdr)
        root.addWidget(make_separator())

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name or employee ID...")
        self.search.textChanged.connect(self._filter)
        root.addWidget(self.search)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Emp ID", "First Name", "Last Name", "DOB", "Category", "Status"])
        for c in range(6):
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        self.status = QLabel("")
        self.status.setObjectName("subtitle")
        root.addWidget(self.status)

        if self.btn_add:
            self.btn_add.clicked.connect(self._add_dialog)
        if self.btn_edit:
            self.btn_edit.clicked.connect(self._edit_dialog)
        if self.btn_del:
            self.btn_del.clicked.connect(self._delete_selected)
        if self.btn_reset:
            self.btn_reset.clicked.connect(self._reset_password)

    def refresh(self):
        with db.get_session() as s:
            emps = s.query(db.Employee).order_by(db.Employee.last_name).all()
            self._all_data = [
                (e.emp_id, e.first_name, e.last_name,
                 str(e.dob) if e.dob else "—", e.category or "—",
                 "Active" if e.is_active else "Inactive")
                for e in emps
            ]
        self._display(self._all_data)
        self.status.setText(f"{len(self._all_data)} employee(s)")

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
        filtered = [r for r in self._all_data
                    if text.lower() in r[0].lower()
                    or text.lower() in r[1].lower()
                    or text.lower() in r[2].lower()]
        self._display(filtered)

    def _employee_dialog(self, edit_id=None):
        dlg = QDialog(self)
        dlg.setWindowTitle("Edit Employee" if edit_id else "Add Employee")
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(12)

        emp_id_edit = QLineEdit()
        fname_edit = QLineEdit()
        lname_edit = QLineEdit()
        dob_edit = QDateEdit()
        dob_edit.setCalendarPopup(True)
        dob_edit.setDate(QDate(1990, 1, 1))
        cat_edit = QLineEdit()
        cat_edit.setPlaceholderText("e.g. Admin, Regular, Manager")

        if edit_id:
            emp_id_edit.setText(edit_id)
            emp_id_edit.setReadOnly(True)

        form.addRow(make_label("Employee ID *"), emp_id_edit)
        form.addRow(make_label("First Name *"), fname_edit)
        form.addRow(make_label("Last Name *"), lname_edit)
        form.addRow(make_label("Date of Birth"), dob_edit)
        form.addRow(make_label("Category"), cat_edit)

        if edit_id:
            with db.get_session() as s:
                emp = s.get(db.Employee, edit_id)
                if emp:
                    fname_edit.setText(emp.first_name)
                    lname_edit.setText(emp.last_name)
                    if emp.dob:
                        dob_edit.setDate(QDate(emp.dob.year, emp.dob.month, emp.dob.day))
                    cat_edit.setText(emp.category or "")

        btns = QHBoxLayout()
        ok = QPushButton("Save")
        ok.setObjectName("success")
        cancel = QPushButton("Cancel")
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(ok)
        form.addRow(btns)

        def save():
            eid = emp_id_edit.text().strip()
            fn = fname_edit.text().strip()
            ln = lname_edit.text().strip()
            if not eid or not fn or not ln:
                QMessageBox.warning(dlg, "Validation", "Employee ID, First Name and Last Name are required.")
                return
            qd = dob_edit.date()
            dob = date(qd.year(), qd.month(), qd.day())
            with db.get_session() as s:
                if edit_id:
                    emp = s.get(db.Employee, edit_id)
                    emp.first_name = fn
                    emp.last_name = ln
                    emp.dob = dob
                    emp.category = cat_edit.text().strip() or None
                else:
                    emp = db.Employee(
                        emp_id=eid, first_name=fn, last_name=ln,
                        dob=dob, category=cat_edit.text().strip() or None,
                        hashed_password=None, must_change_password=True, is_active=True,
                    )
                    s.add(emp)
                s.commit()
            self.refresh()
            dlg.accept()

        ok.clicked.connect(save)
        cancel.clicked.connect(dlg.reject)
        dlg.exec()

    def _add_dialog(self):
        self._employee_dialog()

    def _edit_dialog(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Select an employee to edit.")
            return
        self._employee_dialog(edit_id=self.table.item(row, 0).text())

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        eid = self.table.item(row, 0).text()
        if eid == self.current_user.emp_id:
            QMessageBox.warning(self, "Error", "Cannot delete your own account.")
            return
        name = f"{self.table.item(row, 1).text()} {self.table.item(row, 2).text()}"
        r = QMessageBox.question(self, "Confirm", f"Delete employee '{name}'?")
        if r == QMessageBox.StandardButton.Yes:
            with db.get_session() as s:
                obj = s.get(db.Employee, eid)
                if obj:
                    s.delete(obj)
                    s.commit()
            self.refresh()

    def _reset_password(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Select an employee to reset password.")
            return
        eid = self.table.item(row, 0).text()
        name = f"{self.table.item(row, 1).text()} {self.table.item(row, 2).text()}"
        r = QMessageBox.question(self, "Confirm", f"Reset password for '{name}'?\nThey will be prompted to set a new password on next login.")
        if r == QMessageBox.StandardButton.Yes:
            with db.get_session() as s:
                emp = s.get(db.Employee, eid)
                if emp:
                    emp.hashed_password = None
                    emp.must_change_password = True
                    s.commit()
            QMessageBox.information(self, "Done", "Password reset successfully.")