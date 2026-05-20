from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QDateEdit,
    QComboBox, QMessageBox, QProgressBar, QCheckBox
)
from PySide6.QtCore import Qt, QDate, QThread, Signal as pyqtSignal
from datetime import date, datetime
from .export_utils import (
    build_issues_excel, build_receivables_excel,
    send_email_with_attachment, HAS_OPENPYXL
)
from .email_config_dialog import load_email_config
from ... import db
from ...utils.widgets import make_label, make_separator
import os, tempfile


class _SendWorker(QThread):
    done    = pyqtSignal(bool, str)

    def __init__(self, sender, password, recipient, subject, body, data, filename):
        super().__init__()
        self.sender    = sender
        self.password  = password
        self.recipient = recipient
        self.subject   = subject
        self.body      = body
        self.data      = data
        self.filename  = filename

    def run(self):
        try:
            send_email_with_attachment(
                self.sender, self.password, self.recipient,
                self.subject, self.body, self.data, self.filename
            )
            self.done.emit(True, "Email sent successfully!")
        except Exception as e:
            self.done.emit(False, str(e))


class ExportDialog(QDialog):
    """
    mode: 'issues' or 'receivables'
    """
    def __init__(self, mode: str, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle(f"Export {'Issues' if mode == 'issues' else 'Receivables'}")
        self.setMinimumWidth(480)
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20); root.setSpacing(14)

        title = QLabel(f"Export {'Issues' if self.mode == 'issues' else 'Receivables'} to Excel")
        title.setObjectName("title"); root.addWidget(title)
        root.addWidget(make_separator())

        if not HAS_OPENPYXL:
            root.addWidget(QLabel("⚠  openpyxl not installed. Run: pip install openpyxl"))

        form = QFormLayout(); form.setSpacing(10)

        # Date range
        self.date_from = QDateEdit(); self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setDisplayFormat("dd MMM yyyy")

        self.date_to = QDateEdit(); self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("dd MMM yyyy")

        form.addRow(make_label("From Date"), self.date_from)
        form.addRow(make_label("To Date"),   self.date_to)

        # Status filter (receivables only)
        if self.mode == "receivables":
            self.status_combo = QComboBox()
            self.status_combo.addItem("All Statuses", None)
            for s in ["Ordered", "In Inspection", "Approved"]:
                self.status_combo.addItem(s, s)
            form.addRow(make_label("Status Filter"), self.status_combo)

        root.addLayout(form)
        root.addWidget(make_separator())

        # Email
        email_lbl = QLabel("EMAIL")
        email_lbl.setObjectName("section"); root.addWidget(email_lbl)

        form2 = QFormLayout(); form2.setSpacing(10)
        cfg = load_email_config()

        self.sender_lbl = QLabel(cfg.get("sender", "Not configured"))
        self.sender_lbl.setStyleSheet("color:#38bdf8;")
        form2.addRow(make_label("From"), self.sender_lbl)

        self.recipient_edit = QLineEdit()
        self.recipient_edit.setPlaceholderText("recipient@example.com")
        form2.addRow(make_label("To"), self.recipient_edit)

        self.also_save_cb = QCheckBox("Also save Excel file locally")
        form2.addRow("", self.also_save_cb)

        root.addLayout(form2)

        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True); root.addWidget(self.status_lbl)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0); self.progress.setVisible(False)
        root.addWidget(self.progress)

        btns = QHBoxLayout()
        cfg_btn    = QPushButton("⚙  Email Settings")
        cancel_btn = QPushButton("Cancel")
        send_btn   = QPushButton("📤  Export & Send"); send_btn.setObjectName("primary")
        btns.addWidget(cfg_btn); btns.addStretch()
        btns.addWidget(cancel_btn); btns.addWidget(send_btn)
        root.addLayout(btns)

        cfg_btn.clicked.connect(self._open_email_cfg)
        cancel_btn.clicked.connect(self.reject)
        send_btn.clicked.connect(self._send)

    def _open_email_cfg(self):
        from .email_config_dialog import EmailConfigDialog
        dlg = EmailConfigDialog(self)
        from ...utils.theme import DARK_THEME
        dlg.setStyleSheet(DARK_THEME)
        if dlg.exec():
            cfg = load_email_config()
            self.sender_lbl.setText(cfg.get("sender", ""))

    def _gather_issues(self, d_from, d_to):
        with db.get_session() as s:
            issues = (s.query(db.Issue)
                      .filter(db.Issue.issue_date >= d_from,
                              db.Issue.issue_date <= d_to)
                      .order_by(db.Issue.timestamp)
                      .all())
            result = []
            for iss in issues:
                unit = ""
                if iss.item:
                    mu = iss.item.measurement_unit
                    unit = mu.name if mu else ""
                result.append({
                    "item_code":       iss.item_code,
                    "item_name":       iss.item_name,
                    "measurement_unit": unit,
                    "grade":           iss.grade,
                    "supplier_name":   iss.supplier_name,
                    "quantity_issued": iss.quantity_issued,
                    "unit_price":      iss.unit_price,
                    "total_value":     iss.total_value,
                    "item_group_name": iss.item_group_name,
                    "item_class_name": iss.item_class_name,
                    "issue_date":      iss.issue_date,
                    "timestamp":       iss.timestamp,
                    "submitted_by":    iss.submitted_by,
                    "work_order_name": iss.work_order_name,
                    "contractor_name": iss.contractor_name,
                    "customer_name":   iss.customer_name,
                    "is_adhoc":        iss.is_adhoc,
                })
            return result

    def _gather_receivables(self, d_from, d_to, status_filter):
        with db.get_session() as s:
            q = s.query(db.Receivable).filter(
                db.Receivable.timestamp >= datetime.combine(d_from, datetime.min.time()),
                db.Receivable.timestamp <= datetime.combine(d_to, datetime.max.time()),
            )
            if status_filter:
                q = q.filter(db.Receivable.status == status_filter)
            recs = q.order_by(db.Receivable.timestamp).all()
            result = []
            for rec in recs:
                po_name  = rec.purchase_order.name if rec.purchase_order else ""
                sup_name = rec.supplier.name       if rec.supplier        else ""
                items = []
                for it in rec.items:
                    unit = ""
                    if it.item:
                        mu = it.item.measurement_unit
                        unit = mu.name if mu else ""
                    items.append({
                        "item_code":        it.item_code,
                        "item_name":        it.item_name,
                        "measurement_unit": unit,
                        "grade":            it.grade,
                        "quantity":         it.quantity,
                        "qty_passed":       it.qty_passed,
                        "qty_failed":       it.qty_failed,
                    })
                result.append({
                    "id":             rec.id,
                    "purchase_order": po_name,
                    "supplier":       sup_name,
                    "status":         rec.status,
                    "date":           rec.timestamp.date() if rec.timestamp else "",
                    "submitted_by":   rec.submitted_by or "",
                    "items":          items,
                })
            return result

    def _send(self):
        if not HAS_OPENPYXL:
            QMessageBox.warning(self, "Missing library", "Run: pip install openpyxl"); return

        cfg = load_email_config()
        if not cfg.get("sender") or not cfg.get("app_password"):
            QMessageBox.warning(self, "Email not configured", "Set up Gmail in ⚙ Email Settings first.")
            return

        recipient = self.recipient_edit.text().strip()
        if not recipient:
            QMessageBox.warning(self, "Recipient", "Please enter a recipient email."); return

        qd_from = self.date_from.date(); qd_to = self.date_to.date()
        d_from  = date(qd_from.year(), qd_from.month(), qd_from.day())
        d_to    = date(qd_to.year(),   qd_to.month(),   qd_to.day())
        today   = datetime.now().strftime("%Y-%m-%d")

        if self.mode == "issues":
            data_rows = self._gather_issues(d_from, d_to)
            if not data_rows:
                QMessageBox.information(self, "No data", "No issues found for the selected date range.")
                return
            xlsx_bytes = build_issues_excel(data_rows)
            filename   = f"Issues_{d_from}_{d_to}.xlsx"
            subject    = f"Issues Report — {d_from} to {d_to}"
            body       = f"Please find attached the issues report from {d_from} to {d_to}.\n\nTotal records: {len(data_rows)}"
        else:
            status_filter = self.status_combo.currentData()
            data_rows = self._gather_receivables(d_from, d_to, status_filter)
            if not data_rows:
                QMessageBox.information(self, "No data", "No receivables found for the selected filters.")
                return
            xlsx_bytes = build_receivables_excel(data_rows)
            filename   = f"Receivables_{d_from}_{d_to}.xlsx"
            subject    = f"Receivables Report — {d_from} to {d_to}"
            body       = f"Please find attached the receivables report from {d_from} to {d_to}.\n\nTotal records: {len(data_rows)}"

        # Optionally save locally
        if self.also_save_cb.isChecked():
            save_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
            with open(save_path, "wb") as f:
                f.write(xlsx_bytes)
            self.status_lbl.setText(f"Saved to: {save_path}")
            self.status_lbl.setStyleSheet("color:#4ade80;")

        # Send in background thread
        self.progress.setVisible(True)
        self.status_lbl.setText("Sending email...")
        self.status_lbl.setStyleSheet("color:#94a3b8;")

        self._worker = _SendWorker(
            cfg["sender"], cfg["app_password"],
            recipient, subject, body, xlsx_bytes, filename
        )
        self._worker.done.connect(self._on_send_done)
        self._worker.start()

    def _on_send_done(self, success, msg):
        self.progress.setVisible(False)
        if success:
            self.status_lbl.setText(f"✓  {msg}")
            self.status_lbl.setStyleSheet("color:#4ade80;")
        else:
            self.status_lbl.setText(f"✗  {msg}")
            self.status_lbl.setStyleSheet("color:#f87171;")