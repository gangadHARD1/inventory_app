from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ...auth.auth import authenticate, hash_password, verify_password
from ...db import get_session, Employee
from ...utils.widgets import make_label, make_separator


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inventory Management — Sign In")
        self.setFixedWidth(400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.employee = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.setSpacing(0)

        # Logo / title
        icon = QLabel("⬡")
        icon.setStyleSheet("color:#38bdf8; font-size:36px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(icon)

        title = QLabel("Inventory Management")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        sub = QLabel("Sign in to your account")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(sub)

        root.addSpacing(24)

        root.addWidget(make_label("Employee ID"))
        self.emp_id_edit = QLineEdit()
        self.emp_id_edit.setPlaceholderText("Enter your employee ID")
        root.addWidget(self.emp_id_edit)

        root.addSpacing(12)

        root.addWidget(make_label("Password"))
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setPlaceholderText("Enter your password")
        root.addWidget(self.pass_edit)

        root.addSpacing(6)
        self.hint = QLabel("First login? Leave password blank.")
        self.hint.setObjectName("subtitle")
        root.addWidget(self.hint)

        root.addSpacing(20)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color:#f87171; font-size:12px;")
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl.setWordWrap(True)
        root.addWidget(self.error_lbl)

        self.btn_login = QPushButton("Sign In")
        self.btn_login.setObjectName("primary")
        self.btn_login.setFixedHeight(40)
        root.addWidget(self.btn_login)

        self.btn_login.clicked.connect(self._do_login)
        self.pass_edit.returnPressed.connect(self._do_login)
        self.emp_id_edit.returnPressed.connect(self.pass_edit.setFocus)

    def _do_login(self):
        emp_id = self.emp_id_edit.text().strip()
        password = self.pass_edit.text()
        if not emp_id:
            self.error_lbl.setText("Please enter your Employee ID.")
            return
        emp, err = authenticate(emp_id, password)
        if err == "first_login":
            dlg = SetPasswordDialog(emp, self)
            dlg.exec()
            # Re-authenticate after password set
            emp2, err2 = authenticate(emp_id, dlg.new_password if hasattr(dlg, 'new_password') else "")
            if emp2 and not err2:
                self.employee = emp2
                self.accept()
            else:
                self.error_lbl.setText("Password not set. Please try again.")
            return
        if not emp:
            self.error_lbl.setText(err or "Login failed.")
            return
        if emp.must_change_password:
            dlg = SetPasswordDialog(emp, self)
            dlg.exec()
        self.employee = emp
        self.accept()

    def get_employee(self):
        return self.employee


class SetPasswordDialog(QDialog):
    def __init__(self, employee, parent=None):
        super().__init__(parent)
        self.employee = employee
        self.new_password = ""
        self.setWindowTitle("Set Your Password")
        self.setFixedWidth(380)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(10)

        title = QLabel("🔐  Set Your Password")
        title.setObjectName("title")
        root.addWidget(title)

        msg = QLabel(f"Welcome, {self.employee.first_name}! Please set a password to continue.")
        msg.setObjectName("subtitle")
        msg.setWordWrap(True)
        root.addWidget(msg)
        root.addWidget(make_separator())

        root.addWidget(make_label("New Password"))
        self.pass1 = QLineEdit()
        self.pass1.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass1.setPlaceholderText("At least 6 characters")
        root.addWidget(self.pass1)

        root.addWidget(make_label("Confirm Password"))
        self.pass2 = QLineEdit()
        self.pass2.setEchoMode(QLineEdit.EchoMode.Password)
        root.addWidget(self.pass2)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color:#f87171; font-size:12px;")
        root.addWidget(self.error_lbl)

        btn = QPushButton("Set Password & Continue")
        btn.setObjectName("success")
        btn.setFixedHeight(38)
        btn.clicked.connect(self._save)
        root.addWidget(btn)

    def _save(self):
        p1 = self.pass1.text()
        p2 = self.pass2.text()
        if len(p1) < 6:
            self.error_lbl.setText("Password must be at least 6 characters.")
            return
        if p1 != p2:
            self.error_lbl.setText("Passwords do not match.")
            return
        with get_session() as s:
            emp = s.get(Employee, self.employee.emp_id)
            emp.hashed_password = hash_password(p1)
            emp.must_change_password = False
            s.commit()
        self.new_password = p1
        self.accept()
