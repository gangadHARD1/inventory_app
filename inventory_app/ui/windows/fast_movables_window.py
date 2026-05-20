from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from datetime import date, datetime, timedelta
from sqlalchemy import func
from ...utils.widgets import make_separator
from ... import db


def _last_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _needs_refresh() -> bool:
    """True if cache is empty or was computed before this week's Monday."""
    today = date.today()
    this_monday = _last_monday(today)
    with db.get_session() as s:
        latest = s.query(db.FastMovablesCache).order_by(
            db.FastMovablesCache.computed_on.desc()
        ).first()
        if not latest:
            return True
        return latest.week_start < this_monday


def _recompute():
    today = date.today()
    this_monday = _last_monday(today)
    week_ago = today - timedelta(days=7)

    with db.get_session() as s:
        # Delete old cache
        s.query(db.FastMovablesCache).delete()

        # Aggregate top 20 by quantity in last 7 days
        rows = (
            s.query(
                db.Issue.item_code,
                db.Issue.item_name,
                func.sum(db.Issue.quantity_issued).label("total_qty")
            )
            .filter(db.Issue.issue_date >= week_ago)
            .group_by(db.Issue.item_code, db.Issue.item_name)
            .order_by(func.sum(db.Issue.quantity_issued).desc())
            .limit(20)
            .all()
        )

        now = datetime.now()
        for rank, row in enumerate(rows, start=1):
            s.add(db.FastMovablesCache(
                computed_on=now,
                week_start=this_monday,
                item_code=row.item_code,
                item_name=row.item_name,
                total_qty=row.total_qty,
                rank=rank,
            ))
        s.commit()


def _load_cache():
    with db.get_session() as s:
        rows = s.query(db.FastMovablesCache).order_by(db.FastMovablesCache.rank).all()
        return [(r.rank, r.item_code, r.item_name, r.total_qty, r.week_start, r.computed_on) for r in rows]


class FastMovablesWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fast Movables — Top 20 Items (Last 7 Days)")
        self.resize(780, 580)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("⚡  Fast Movables")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()
        self.btn_force = QPushButton("↺  Force Refresh")
        self.btn_force.clicked.connect(self._force_refresh)
        hdr.addWidget(self.btn_force)
        root.addLayout(hdr)

        self.meta_lbl = QLabel("")
        self.meta_lbl.setObjectName("subtitle")
        root.addWidget(self.meta_lbl)
        root.addWidget(make_separator())

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Rank", "Item Code", "Item Name", "Total Qty Issued", ""])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        self.status_lbl = QLabel("")
        self.status_lbl.setObjectName("subtitle")
        root.addWidget(self.status_lbl)

    def _refresh(self, force=False):
        if force or _needs_refresh():
            _recompute()
        rows = _load_cache()
        self._populate(rows)

    def _force_refresh(self):
        self._refresh(force=True)

    def _populate(self, rows):
        self.table.setRowCount(0)
        if not rows:
            self.status_lbl.setText("No issues found in the last 7 days.")
            self.meta_lbl.setText("")
            return

        # Show meta info
        week_start = rows[0][4]
        computed_on = rows[0][5]
        self.meta_lbl.setText(
            f"Week of {week_start.strftime('%d %b %Y')}  ·  "
            f"Computed: {computed_on.strftime('%d %b %Y %H:%M')}"
        )

        max_qty = rows[0][3] if rows else 1

        for rank, item_code, item_name, total_qty, _, _ in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)

            # Rank with medal for top 3
            rank_str = {1: "🥇 1", 2: "🥈 2", 3: "🥉 3"}.get(rank, str(rank))
            rank_item = QTableWidgetItem(rank_str)
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 0, rank_item)

            self.table.setItem(r, 1, QTableWidgetItem(item_code))
            self.table.setItem(r, 2, QTableWidgetItem(item_name))

            qty_item = QTableWidgetItem(f"{total_qty:,.2f}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            # Color by rank
            if rank <= 3:
                qty_item.setForeground(QColor("#38bdf8"))
            elif rank <= 10:
                qty_item.setForeground(QColor("#4ade80"))
            self.table.setItem(r, 3, qty_item)

            # Progress bar cell
            bar = QProgressBar()
            bar.setRange(0, 100)
            pct = int((total_qty / max_qty) * 100) if max_qty > 0 else 0
            bar.setValue(pct)
            bar.setTextVisible(False)
            bar.setFixedHeight(8)
            bar.setStyleSheet("""
                QProgressBar { background:#1e2330; border-radius:4px; border:none; }
                QProgressBar::chunk { background:#38bdf8; border-radius:4px; }
            """)
            bar_widget = QWidget()
            bar_layout = QHBoxLayout(bar_widget)
            bar_layout.setContentsMargins(8, 0, 8, 0)
            bar_layout.addWidget(bar)
            self.table.setCellWidget(r, 4, bar_widget)
            self.table.setRowHeight(r, 38)

        self.status_lbl.setText(f"Showing top {len(rows)} items  ·  Updates every Monday")
