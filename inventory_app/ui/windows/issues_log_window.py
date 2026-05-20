from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QHeaderView, QDateEdit, QComboBox, QFrame
)
from PySide6.QtCore import Qt, QDate
from ...utils.widgets import make_label, make_separator
from ... import db


class IssuesLogWindow(QWidget):
    def __init__(self, current_user, parent=None):
        self.current_user = current_user
        super().__init__(parent)
        self.setWindowTitle("Issues Log")
        self.resize(1100, 620)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        hdr = QHBoxLayout()
        title = QLabel("Issues Log")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()
        self.btn_refresh = QPushButton("↺  Refresh")
        self.btn_refresh.setObjectName("primary")
        hdr.addWidget(self.btn_refresh)
        root.addLayout(hdr)
        root.addWidget(make_separator())

        # Filter row
        filter_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search item, supplier, contractor...")
        filter_row.addWidget(self.search, 2)

        filter_row.addWidget(make_label("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setDisplayFormat("dd MMM yyyy")
        filter_row.addWidget(self.date_from)

        filter_row.addWidget(make_label("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("dd MMM yyyy")
        filter_row.addWidget(self.date_to)

        self.btn_filter = QPushButton("Filter")
        self.btn_filter.setObjectName("primary")
        filter_row.addWidget(self.btn_filter)
        root.addLayout(filter_row)

        # Table
        cols = [
            "ID", "Timestamp", "Issue Date", "Item Name", "Item Code",
            "Grade", "Qty", "Unit Price", "Total Value",
            "Item Class", "Item Group", "Supplier",
            "Work Order", "Contractor", "Customer","Issued By"
        ]
        self.table = QTableWidget()
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        # Stats bar
        self.stats_bar = QLabel("")
        self.stats_bar.setObjectName("subtitle")
        root.addWidget(self.stats_bar)

        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_filter.clicked.connect(self.refresh)
        self.search.textChanged.connect(self._filter_table)

    def refresh(self):
        from datetime import date
        qd_from = self.date_from.date()
        qd_to = self.date_to.date()
        d_from = date(qd_from.year(), qd_from.month(), qd_from.day())
        d_to = date(qd_to.year(), qd_to.month(), qd_to.day())

        with db.get_session() as s:
            issues = (s.query(db.Issue)
                      .filter(db.Issue.issue_date >= d_from, db.Issue.issue_date <= d_to)
                      .order_by(db.Issue.timestamp.desc())
                      .all())
            self._all_rows = []
            total_val = 0
            for iss in issues:
                total_val += iss.total_value or 0
                self._all_rows.append((
                    str(iss.id),
                    iss.timestamp.strftime("%d %b %Y %H:%M") if iss.timestamp else "—",
                    str(iss.issue_date),
                    iss.item_name or "—",
                    iss.item_code or "—",
                    iss.grade or "—",
                    f"{iss.quantity_issued:,.2f}",
                    f"₹{iss.unit_price:,.2f}",
                    f"₹{iss.total_value:,.2f}",
                    iss.item_class_name or "—",
                    iss.item_group_name or "—",
                    iss.supplier_name or "—",
                    iss.work_order_name or "—",
                    iss.contractor_name or "—",
                    iss.customer_name or "—",
                    iss.submitted_by or "—",
                ))

        self._display(self._all_rows)
        self.stats_bar.setText(
            f"{len(self._all_rows)} issue(s)  ·  Total Value: ₹{total_val:,.2f}"
        )

    def _display(self, rows):
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r, c, item)

    def _filter_table(self, text):
        if not text:
            self._display(self._all_rows)
            return
        filtered = [
            row for row in self._all_rows
            if any(text.lower() in cell.lower() for cell in row)
        ]
        self._display(filtered)