from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QGridLayout, QSizePolicy, QStatusBar
)
from PySide6.QtCore import Qt, QSize
from ..utils.widgets import make_separator, StatCard
from ..utils.theme import DARK_THEME
from ..auth.auth import can as auth_can, is_superuser
from .. import db


class NavButton(QPushButton):
    def __init__(self, icon, label, parent=None):
        super().__init__(parent)
        self.setText(f"{icon}\n{label}")
        self.setFixedSize(QSize(150, 100))
        self.setStyleSheet("""
            QPushButton {
                background-color: #131720; border: 1px solid #1e2330;
                border-radius: 10px; color: #94a3b8;
                font-size: 12px; font-weight: 500; padding: 10px;
            }
            QPushButton:hover { background-color: #1a2035; border-color: #38bdf8; color: #f1f5f9; }
            QPushButton:pressed { background-color: #0e1729; }
        """)


class MainDashboard(QMainWindow):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle(f"Inventory Management  —  {current_user.first_name} {current_user.last_name}")
        self.setMinimumSize(900, 600)
        self.resize(1060, 700)
        self._open_windows = {}
        self._build_ui()
        self._refresh_stats()

    def _can(self, table, action="view"):
        return auth_can(self.current_user.category, table, action)

    def _super(self):
        return is_superuser(self.current_user.category)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar
        top = QFrame()
        top.setObjectName("top_bar")
        top.setFixedHeight(64)
        tl = QHBoxLayout(top)
        tl.setContentsMargins(28, 0, 28, 0)

        btn_export_issues = QPushButton("📊 Export Issues")
        btn_export_issues.clicked.connect(self._export_issues)
        btn_export_recv = QPushButton("📦 Export Receivables")
        btn_export_recv.clicked.connect(self._export_receivables)
        tl.addWidget(btn_export_issues)
        tl.addWidget(btn_export_recv)

        app_title = QLabel("⬡  Inventory Management")
        app_title.setObjectName("title")
        tl.addWidget(app_title)
        tl.addStretch()

        user_lbl = QLabel(f"{self.current_user.first_name} {self.current_user.last_name}  ·  {self.current_user.category or ''}")
        user_lbl.setObjectName("subtitle")
        tl.addWidget(user_lbl)
        tl.addSpacing(16)

        if self._can("issues", "add"):
            self.btn_new_issue = QPushButton("＋  New Issue")
            self.btn_new_issue.setObjectName("primary")
            self.btn_new_issue.setFixedWidth(130)
            self.btn_new_issue.clicked.connect(self._open_new_issue)
            tl.addWidget(self.btn_new_issue)

        root.addWidget(top)

        # Body
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(32, 28, 32, 28)
        body_layout.setSpacing(24)

        self.stats_frame = QHBoxLayout()
        self.stats_frame.setSpacing(12)
        body_layout.addLayout(self.stats_frame)
        body_layout.addWidget(make_separator())

        nav_lbl = QLabel("MANAGE RECORDS")
        nav_lbl.setObjectName("section")
        body_layout.addWidget(nav_lbl)

        nav_grid = QGridLayout()
        nav_grid.setSpacing(12)

        nav_items = [
            ("📦", "Items",              self._open_items,           self._can("items")),
            ("🏭", "Item Classes",       self._open_item_classes,    self._can("item_classes")),
            ("🗂", "Item Groups",        self._open_item_groups,     self._can("item_groups")),
            ("🤝", "Contractors",        self._open_contractors,     self._can("contractors")),
            ("👥", "Customers",          self._open_customers,       self._can("customers")),
            ("🚚", "Suppliers",          self._open_suppliers,       self._can("suppliers")),
            ("📋", "Work Orders",        self._open_work_orders,     self._can("work_orders")),
            ("🏷", "WO Categories",      self._open_wo_categories,   self._can("work_order_categories")),
            ("📐", "Measurement Units", self._open_meas_units,      self._can("measurement_units")),
            ("👤", "Employees",          self._open_employees,       self._can("employees") or self._super()),
            ("📜", "Issues Log",         self._open_issues_log,      self._can("issues")),
            ("⚡", "Fast Movables",      self._open_fast_movables,   self._can("issues")),
            ("🔐", "Role Permissions",   self._open_roles,           self._super()),
            ("📥", "New Receivable",     self._open_receivable_form,  True),
            ("🔄", "Change Status",      self._open_change_status,    True),
            ("📋", "Receivables Log",    self._open_receivables_log,  True),
            ("🧾", "Purchase Orders",    self._open_purchase_orders,  True),
        ]

        col = 0
        row = 0
        for icon, label, handler, visible in nav_items:
            if not visible:
                continue
            btn = NavButton(icon, label)
            btn.clicked.connect(handler)
            nav_grid.addWidget(btn, row, col)
            col += 1
            if col >= 5:
                col = 0
                row += 1

        body_layout.addLayout(nav_grid)
        body_layout.addStretch()
        root.addWidget(body)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"Logged in as {self.current_user.emp_id}  ({self.current_user.category})")

    def _refresh_stats(self):
        while self.stats_frame.count():
            item = self.stats_frame.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        try:
            with db.get_session() as s:
                from sqlalchemy import func
                n_items = s.query(db.Item).count()
                n_issues = s.query(db.Issue).count()
                n_contractors = s.query(db.Contractor).count()
                n_suppliers = s.query(db.Supplier).count()
                total_val = s.query(func.sum(db.Issue.total_value)).scalar() or 0
            self.stats_frame.addWidget(StatCard("Items", str(n_items)))
            self.stats_frame.addWidget(StatCard("Total Issues", str(n_issues), "#a78bfa"))
            self.stats_frame.addWidget(StatCard("Contractors", str(n_contractors), "#34d399"))
            self.stats_frame.addWidget(StatCard("Suppliers", str(n_suppliers), "#f59e0b"))
            self.stats_frame.addWidget(StatCard("Total Issued Value", f"₹{total_val:,.0f}", "#f87171"))
            self.stats_frame.addStretch()
        except Exception:
            pass

    def _open_window(self, key, cls, *args):
        if key in self._open_windows and not self._open_windows[key].isHidden():
            self._open_windows[key].raise_()
            self._open_windows[key].activateWindow()
            return
        win = cls(*args)
        win.setStyleSheet(DARK_THEME)
        win.show()
        self._open_windows[key] = win
    def _export_issues(self):
        from ..ui.dialogs.export_dialog import ExportDialog
        dlg = ExportDialog(mode="issues", parent=self)
        dlg.setStyleSheet(DARK_THEME)
        dlg.exec()

    def _export_receivables(self):
        from ..ui.dialogs.export_dialog import ExportDialog
        dlg = ExportDialog(mode="receivables", parent=self)
        dlg.setStyleSheet(DARK_THEME)
        dlg.exec()

    def _open_items(self):
        from ..ui.windows.items_window import ItemsWindow
        self._open_window("items", ItemsWindow, self.current_user)

    def _open_item_classes(self):
        from ..ui.windows.simple_tables import ItemClassesWindow
        self._open_window("item_classes", ItemClassesWindow, self.current_user)

    def _open_item_groups(self):
        from ..ui.windows.simple_tables import ItemGroupsWindow
        self._open_window("item_groups", ItemGroupsWindow, self.current_user)

    def _open_contractors(self):
        from ..ui.windows.simple_tables import ContractorsWindow
        self._open_window("contractors", ContractorsWindow, self.current_user)

    def _open_customers(self):
        from ..ui.windows.simple_tables import CustomersWindow
        self._open_window("customers", CustomersWindow, self.current_user)

    def _open_suppliers(self):
        from ..ui.windows.simple_tables import SuppliersWindow
        self._open_window("suppliers", SuppliersWindow, self.current_user)

    def _open_work_orders(self):
        from ..ui.windows.work_orders_window import WorkOrdersWindow
        self._open_window("work_orders", WorkOrdersWindow, self.current_user)

    def _open_wo_categories(self):
        from ..ui.windows.simple_tables import WOCategoriesWindow
        self._open_window("wo_categories", WOCategoriesWindow, self.current_user)

    def _open_meas_units(self):
        from ..ui.windows.simple_tables import MeasurementUnitsWindow
        self._open_window("meas_units", MeasurementUnitsWindow, self.current_user)

    def _open_employees(self):
        from ..ui.windows.employees_window import EmployeesWindow
        self._open_window("employees", EmployeesWindow, self.current_user)

    def _open_issues_log(self):
        from ..ui.windows.issues_log_window import IssuesLogWindow
        self._open_window("issues_log", IssuesLogWindow, self.current_user)

    def _open_fast_movables(self):
        from ..ui.windows.fast_movables_window import FastMovablesWindow
        self._open_window("fast_movables", FastMovablesWindow)

    def _open_roles(self):
        from ..ui.windows.roles_window import RolesWindow
        self._open_window("roles", RolesWindow)

    def _open_new_issue(self):
        from ..ui.windows.issue_form_window import IssueFormWindow
        win = IssueFormWindow(self.current_user)
        win.setStyleSheet(DARK_THEME)
        win.issue_submitted.connect(self._refresh_stats)
        win.show()
        self._open_windows["issue_form"] = win
    def _open_receivable_form(self):
        from ..ui.windows.receivable_form_window import ReceivableFormWindow
        win = ReceivableFormWindow(self.current_user)
        win.setStyleSheet(DARK_THEME); win.show()
        self._open_windows["receivable_form"] = win

    def _open_change_status(self):
        from ..ui.windows.change_status_window import ChangeStatusWindow
        self._open_window("change_status", ChangeStatusWindow, self.current_user)

    def _open_receivables_log(self):
        from ..ui.windows.receivables_log_window import ReceivablesLogWindow
        self._open_window("receivables_log", ReceivablesLogWindow, self.current_user)

    def _open_purchase_orders(self):
        from ..ui.windows.purchase_orders_window import PurchaseOrdersWindow
        self._open_window("purchase_orders", PurchaseOrdersWindow, self.current_user)