from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QLabel, QHBoxLayout, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from ...utils.widgets import make_label, make_separator
from ... import db


class DBConfigDialog(QDialog):
    def __init__(self, existing_config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Configuration")
        self.setMinimumWidth(440)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._config = existing_config or {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel("PostgreSQL Connection")
        title.setObjectName("title")
        root.addWidget(title)

        sub = QLabel("Configure your database connection. Settings will be saved locally.")
        sub.setObjectName("subtitle")
        sub.setWordWrap(True)
        root.addWidget(sub)
        root.addWidget(make_separator())

        form = QFormLayout()
        form.setSpacing(10)

        self.host_edit = QLineEdit(self._config.get("host", "localhost"))
        self.port_edit = QLineEdit(str(self._config.get("port", "5432")))
        self.dbname_edit = QLineEdit(self._config.get("dbname", "inventory"))
        self.user_edit = QLineEdit(self._config.get("user", "postgres"))
        self.pass_edit = QLineEdit(self._config.get("password", ""))
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow(make_label("Host"), self.host_edit)
        form.addRow(make_label("Port"), self.port_edit)
        form.addRow(make_label("Database Name"), self.dbname_edit)
        form.addRow(make_label("Username"), self.user_edit)
        form.addRow(make_label("Password"), self.pass_edit)
        root.addLayout(form)

        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        root.addWidget(self.status_lbl)

        btns = QHBoxLayout()
        self.btn_test = QPushButton("Test Connection")
        self.btn_save = QPushButton("Save & Connect")
        self.btn_save.setObjectName("primary")

        btns.addWidget(self.btn_test)
        btns.addStretch()
        btns.addWidget(self.btn_save)
        root.addLayout(btns)

        self.btn_test.clicked.connect(self._test)
        self.btn_save.clicked.connect(self._save)

    def _get_config(self):
        return {
            "host": self.host_edit.text().strip(),
            "port": self.port_edit.text().strip(),
            "dbname": self.dbname_edit.text().strip(),
            "user": self.user_edit.text().strip(),
            "password": self.pass_edit.text(),
            "dialect": "postgresql",
        }

    def _test(self):
        config = self._get_config()
        self.status_lbl.setText("Testing...")
        self.status_lbl.setStyleSheet("color: #94a3b8;")
        ok, msg = db.test_connection(config)
        if ok:
            self.status_lbl.setText(f"✓  {msg}")
            self.status_lbl.setStyleSheet("color: #4ade80;")
        else:
            self.status_lbl.setText(f"✗  {msg}")
            self.status_lbl.setStyleSheet("color: #f87171;")

    def _save(self):
        config = self._get_config()
        if not all([config["host"], config["port"], config["dbname"], config["user"]]):
            QMessageBox.warning(self, "Validation", "Host, Port, Database Name and Username are required.")
            return
        ok, msg = db.test_connection(config)
        if not ok:
            r = QMessageBox.question(
                self, "Connection Failed",
                f"Could not connect:\n{msg}\n\nSave anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if r != QMessageBox.StandardButton.Yes:
                return
        db.save_config(config)
        self._config = config
        self.accept()

    def get_config(self):
        return self._config
