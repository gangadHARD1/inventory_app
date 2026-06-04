import sys
import os

# PyInstaller one-file: ensure project root is on path when frozen.
if getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.dirname(os.path.abspath(sys.executable)))
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFont
from inventory_app.utils.theme import DARK_THEME
from inventory_app.ui.dialogs.login_dialog import LoginDialog
from inventory_app.ui.main_dashboard import MainDashboard
from inventory_app import db
from inventory_app.auth.auth import seed_admin


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Inventory Management System")
    app.setStyleSheet(DARK_THEME)
    app.setFont(QFont("Segoe UI", 10))

    # Init DB (creates tables)
    try:
        db.init_db()
    except Exception as e:
        QMessageBox.critical(None, "DB Error", f"Could not initialize database:\n{e}")
        sys.exit(1)

    # Seed default admin if needed
    seed_admin()

    # Login loop
    while True:
        dlg = LoginDialog()
        dlg.setStyleSheet(DARK_THEME)
        if dlg.exec() != LoginDialog.DialogCode.Accepted:
            sys.exit(0)
        employee = dlg.get_employee()
        if employee:
            break

    dashboard = MainDashboard(employee)
    dashboard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()