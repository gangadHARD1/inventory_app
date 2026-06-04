from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QHBoxLayout, QLabel, QMessageBox
)
from PySide6.QtCore import Qt
import json
import os
import shutil

from ...paths import app_data_dir, bundle_dir

CONFIG_PATH = os.path.join(app_data_dir(), "email_config.json")


def _ensure_email_config():
    if os.path.exists(CONFIG_PATH):
        return
    bundled = os.path.join(bundle_dir(), "inventory_app", "email_config.json")
    if os.path.isfile(bundled):
        shutil.copy2(bundled, CONFIG_PATH)


def load_email_config():
    _ensure_email_config()
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_email_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


class EmailConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Email Settings")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20); root.setSpacing(12)

        title = QLabel("Gmail Configuration"); title.setObjectName("title")
        root.addWidget(title)

        note = QLabel(
            "Use a Gmail App Password (not your regular password).\n"
            "Generate at: Google Account → Security → 2-Step Verification → App Passwords"
        )
        note.setObjectName("subtitle"); note.setWordWrap(True)
        root.addWidget(note)

        form = QFormLayout(); form.setSpacing(10)
        cfg = load_email_config()

        self.sender_edit = QLineEdit(cfg.get("sender", ""))
        self.sender_edit.setPlaceholderText("yourname@gmail.com")
        self.apppass_edit = QLineEdit(cfg.get("app_password", ""))
        self.apppass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.apppass_edit.setPlaceholderText("xxxx xxxx xxxx xxxx")

        from ...utils.widgets import make_label
        form.addRow(make_label("Gmail Address"), self.sender_edit)
        form.addRow(make_label("App Password"),  self.apppass_edit)
        root.addLayout(form)

        self.status_lbl = QLabel(""); self.status_lbl.setWordWrap(True)
        root.addWidget(self.status_lbl)

        btns = QHBoxLayout()
        test_btn = QPushButton("Test Connection")
        save_btn = QPushButton("Save"); save_btn.setObjectName("primary")
        btns.addWidget(test_btn); btns.addStretch(); btns.addWidget(save_btn)
        root.addLayout(btns)

        test_btn.clicked.connect(self._test)
        save_btn.clicked.connect(self._save)

    def _test(self):
        import smtplib
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(self.sender_edit.text().strip(),
                           self.apppass_edit.text().strip())
            self.status_lbl.setText("✓  Connection successful!")
            self.status_lbl.setStyleSheet("color:#4ade80;")
        except Exception as e:
            self.status_lbl.setText(f"✗  {e}")
            self.status_lbl.setStyleSheet("color:#f87171;")

    def _save(self):
        cfg = {
            "sender":       self.sender_edit.text().strip(),
            "app_password": self.apppass_edit.text().strip(),
        }
        if not cfg["sender"] or not cfg["app_password"]:
            QMessageBox.warning(self, "Validation", "Both fields are required.")
            return
        save_email_config(cfg)
        self.accept()