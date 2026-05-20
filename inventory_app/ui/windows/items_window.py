from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout, QDoubleSpinBox,
    QHeaderView, QMessageBox, QGroupBox, QScrollArea, QFrame,
    QComboBox, QDateEdit, QTextEdit, QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QDate
from ...utils.widgets import make_label, make_separator
from ... import db
from ...auth.auth import can as auth_can, is_superuser
from datetime import date


class ItemsWindow(QWidget):
    def __init__(self, current_user, parent=None):
        self.current_user = current_user
        super().__init__(parent)
        self.setWindowTitle("Items")
        self.resize(1000, 600)
        self._build_ui()
        self.refresh()

    def _can(self, action):
        return auth_can(self.current_user.category, "items", action) or is_superuser(self.current_user.category)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("Items"); title.setObjectName("title")
        hdr.addWidget(title); hdr.addStretch()
        if self._can("add"):
            self.btn_add = QPushButton("＋  Add Item"); self.btn_add.setObjectName("primary")
            hdr.addWidget(self.btn_add)
        else: self.btn_add = None
        if self._can("edit"):
            self.btn_edit = QPushButton("✎  Edit"); hdr.addWidget(self.btn_edit)
        else: self.btn_edit = None
        if self._can("delete"):
            self.btn_del = QPushButton("✕  Delete"); self.btn_del.setObjectName("danger")
            hdr.addWidget(self.btn_del)
        else: self.btn_del = None
        root.addLayout(hdr)
        root.addWidget(make_separator())

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name or code...")
        self.search.textChanged.connect(self._filter)
        root.addWidget(self.search)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Item Code", "Item Name", "Unit", "Base Price", "Total Qty", "Grades", "Suppliers"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._edit_dialog)
        root.addWidget(self.table)

        self.status = QLabel(""); self.status.setObjectName("subtitle")
        root.addWidget(self.status)

        if self.btn_add:  self.btn_add.clicked.connect(self._add_dialog)
        if self.btn_edit: self.btn_edit.clicked.connect(self._edit_dialog)
        if self.btn_del:  self.btn_del.clicked.connect(self._delete_selected)

    def refresh(self):
        with db.get_session() as s:
            items = s.query(db.Item).order_by(db.Item.item_name).all()
            self._all_data = []
            for item in items:
                unit_name = item.measurement_unit.name if item.measurement_unit else "—"
                grade_str = ", ".join(
                    f"{g.grade}(₹{g.unit_price:.2f}, qty:{g.quantity:.2f})" for g in item.grades
                ) or "—"
                sup_str = ", ".join(
                    f"{isup.supplier.name}({isup.quantity})" for isup in item.item_suppliers
                ) or "—"
                self._all_data.append((
                    item.item_code, item.item_name, unit_name,
                    item.unit_price, item.quantity_in_store, grade_str, sup_str
                ))
        self._display(self._all_data)
        self.status.setText(f"{len(self._all_data)} item(s)")

    def _display(self, rows):
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount(); self.table.insertRow(r)
            vals = [
                str(row[0]), str(row[1]), str(row[2]),
                f"₹{row[3]:.2f}" if row[3] is not None else "—",
                str(row[4] or 0), str(row[5]), str(row[6])
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r, c, item)

    def _filter(self, text):
        filtered = [r for r in self._all_data
                    if text.lower() in r[0].lower() or text.lower() in r[1].lower()]
        self._display(filtered)

    def _item_dialog(self, edit_code=None):
        dlg = QDialog(self)
        dlg.setWindowTitle("Edit Item" if edit_code else "Add Item")
        dlg.setMinimumSize(720, 680)

        root = QVBoxLayout(dlg)
        root.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        root.addWidget(tabs)

        # ── Tab 1: Core ───────────────────────────────────────────────────────
        tab_core = QWidget()
        tc = QVBoxLayout(tab_core)
        tc.setContentsMargins(20, 16, 20, 16); tc.setSpacing(10)

        grid1 = QHBoxLayout()
        lc = QFormLayout(); lc.setSpacing(8)
        w_code  = QLineEdit()
        w_name  = QLineEdit()
        w_price = QDoubleSpinBox(); w_price.setRange(0, 9999999); w_price.setDecimals(2); w_price.setPrefix("₹ ")
        w_qty   = QDoubleSpinBox(); w_qty.setRange(0, 9999999); w_qty.setDecimals(2)

        w_unit = QComboBox()
        w_unit.addItem("— Select Unit *", None)
        with db.get_session() as s:
            for u in s.query(db.MeasurementUnit).order_by(db.MeasurementUnit.name).all():
                w_unit.addItem(u.name, u.id)

        if edit_code:
            w_code.setText(edit_code); w_code.setReadOnly(True)

        lc.addRow(make_label("Item Code *"), w_code)
        lc.addRow(make_label("Item Name *"), w_name)
        lc.addRow(make_label("Measurement Unit *"), w_unit)
        lc.addRow(make_label("Base Unit Price (₹)"), w_price)
        lc.addRow(make_label("Non-graded Qty in Store"), w_qty)

        rc = QFormLayout(); rc.setSpacing(8)
        w_sec_type = QLineEdit()
        w_sec_code = QLineEdit()
        w_location = QLineEdit()
        w_remark   = QTextEdit(); w_remark.setMaximumHeight(80)
        w_last_upd = QLineEdit(self.current_user.emp_id); w_last_upd.setReadOnly(True)

        rc.addRow(make_label("Section Type"), w_sec_type)
        rc.addRow(make_label("Section Code"), w_sec_code)
        rc.addRow(make_label("Location"), w_location)
        rc.addRow(make_label("Last Update By"), w_last_upd)
        rc.addRow(make_label("Remark"), w_remark)

        grid1.addLayout(lc, 1); grid1.addSpacing(16); grid1.addLayout(rc, 1)
        tc.addLayout(grid1)
        tabs.addTab(tab_core, "Core")

        # ── Tab 2: Dimensions ─────────────────────────────────────────────────
        tab_dim = QWidget()
        td = QFormLayout(tab_dim)
        td.setContentsMargins(20, 16, 20, 16); td.setSpacing(8)

        def dspin():
            sp = QDoubleSpinBox(); sp.setRange(0, 9999999); sp.setDecimals(4)
            sp.setSpecialValueText("—"); return sp

        w_sec_size   = dspin(); w_length     = dspin(); w_scrap_len  = dspin()
        w_width      = dspin(); w_height     = dspin(); w_depth      = dspin()
        w_thickness  = dspin(); w_weight     = dspin(); w_wt_tonne   = dspin()
        w_avail_wt   = dspin(); w_req_wt     = dspin(); w_surf_area  = dspin()
        w_cross_area = dspin(); w_area       = dspin(); w_density    = dspin()

        for label, widget in [
            ("Section Size", w_sec_size), ("Length", w_length), ("Scrap Length", w_scrap_len),
            ("Width", w_width), ("Height", w_height), ("Depth", w_depth),
            ("Thickness", w_thickness), ("Weight", w_weight), ("Weight in Tonne", w_wt_tonne),
            ("Available Weight", w_avail_wt), ("Required Weight", w_req_wt),
            ("Surface Area", w_surf_area), ("Cross Section Area", w_cross_area),
            ("Area", w_area), ("Density", w_density),
        ]:
            td.addRow(make_label(label), widget)
        tabs.addTab(tab_dim, "Dimensions & Weight")

        # ── Tab 3: Dates ──────────────────────────────────────────────────────
        tab_dates = QWidget()
        tdt = QFormLayout(tab_dates)
        tdt.setContentsMargins(20, 16, 20, 16); tdt.setSpacing(8)
        sentinel = QDate(2000, 1, 1)
        w_po_date   = QDateEdit(); w_po_date.setCalendarPopup(True); w_po_date.setDate(sentinel)
        w_last_date = QDateEdit(); w_last_date.setCalendarPopup(True); w_last_date.setDate(sentinel)
        tdt.addRow(make_label("PO Receipt Date"), w_po_date)
        tdt.addRow(make_label("Last Date"), w_last_date)
        tabs.addTab(tab_dates, "Dates")

        # ── Tab 4: Grades ─────────────────────────────────────────────────────
        tab_grades = QWidget()
        tg = QVBoxLayout(tab_grades)
        tg.setContentsMargins(20, 12, 20, 12); tg.setSpacing(8)

        # Column headers
        col_hdr = QHBoxLayout()
        col_hdr.addWidget(QLabel("Grade Name"), 2)
        col_hdr.addWidget(QLabel("Unit Price (₹)"), 1)
        col_hdr.addWidget(QLabel("Quantity"), 1)
        col_hdr.addWidget(QLabel(""), )
        tg.addLayout(col_hdr)

        grade_rows = []
        grade_scroll = QScrollArea(); grade_scroll.setWidgetResizable(True)
        grade_scroll.setFrameShape(QFrame.Shape.NoFrame)
        grade_container = QWidget()
        grade_cl = QVBoxLayout(grade_container)
        grade_cl.setContentsMargins(0, 0, 0, 0); grade_cl.setSpacing(4)
        grade_scroll.setWidget(grade_container)

        def add_grade_row(grade="", price=0.0, qty=0.0):
            row_w = QWidget()
            rl = QHBoxLayout(row_w); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(6)
            ge = QLineEdit(grade); ge.setPlaceholderText("Grade name e.g. A1")
            pe = QDoubleSpinBox(); pe.setRange(0, 9999999); pe.setDecimals(2); pe.setValue(price)
            qe = QDoubleSpinBox(); qe.setRange(0, 9999999); qe.setDecimals(2); qe.setValue(qty)
            rb = QPushButton("✕"); rb.setObjectName("icon_btn"); rb.setFixedWidth(28)
            rb.clicked.connect(lambda: (grade_rows.remove(row_w), row_w.setParent(None), row_w.deleteLater()))
            rl.addWidget(ge, 2); rl.addWidget(pe, 1); rl.addWidget(qe, 1); rl.addWidget(rb)
            grade_rows.append(row_w)
            grade_cl.addWidget(row_w)
            row_w._grade_edit = ge; row_w._price_edit = pe; row_w._qty_edit = qe

        note_g = QLabel("Grade quantities + non-graded qty = total qty in store.")
        note_g.setObjectName("subtitle"); note_g.setWordWrap(True)
        btn_ag = QPushButton("＋  Add Grade"); btn_ag.setObjectName("primary")
        btn_ag.clicked.connect(lambda: add_grade_row())
        tg.addWidget(note_g); tg.addWidget(btn_ag); tg.addWidget(grade_scroll)
        tabs.addTab(tab_grades, "Grades")

        # ── Tab 5: Suppliers ──────────────────────────────────────────────────
        tab_sups = QWidget()
        ts = QVBoxLayout(tab_sups)
        ts.setContentsMargins(20, 12, 20, 12); ts.setSpacing(8)
        sup_rows = []
        sup_scroll = QScrollArea(); sup_scroll.setWidgetResizable(True)
        sup_scroll.setFrameShape(QFrame.Shape.NoFrame)
        sup_container = QWidget()
        sup_cl = QVBoxLayout(sup_container)
        sup_cl.setContentsMargins(0, 0, 0, 0); sup_cl.setSpacing(4)
        sup_scroll.setWidget(sup_container)

        with db.get_session() as s:
            all_suppliers = [(sup.id, sup.name) for sup in s.query(db.Supplier).order_by(db.Supplier.name).all()]

        def add_sup_row(sup_id=None, qty=0.0):
            row_w = QWidget()
            rl = QHBoxLayout(row_w); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(6)
            sc = QComboBox()
            for sid, sname in all_suppliers:
                sc.addItem(sname, sid)
            if sup_id:
                idx = sc.findData(sup_id)
                if idx >= 0: sc.setCurrentIndex(idx)
            qe = QDoubleSpinBox(); qe.setRange(0, 9999999); qe.setDecimals(2); qe.setValue(qty)
            rb = QPushButton("✕"); rb.setObjectName("icon_btn"); rb.setFixedWidth(28)
            rb.clicked.connect(lambda: (sup_rows.remove(row_w), row_w.setParent(None), row_w.deleteLater()))
            rl.addWidget(QLabel("Supplier:")); rl.addWidget(sc, 2)
            rl.addWidget(QLabel("Qty:")); rl.addWidget(qe, 1); rl.addWidget(rb)
            sup_rows.append(row_w)
            sup_cl.addWidget(row_w)
            row_w._sup_combo = sc; row_w._qty_edit = qe

        note_s = QLabel("Supplier quantities are independent of grade quantities.")
        note_s.setObjectName("subtitle"); note_s.setWordWrap(True)
        btn_as = QPushButton("＋  Add Supplier"); btn_as.setObjectName("primary")
        btn_as.clicked.connect(lambda: add_sup_row())
        ts.addWidget(note_s); ts.addWidget(btn_as); ts.addWidget(sup_scroll)
        tabs.addTab(tab_sups, "Suppliers")

        # ── Pre-fill if editing ───────────────────────────────────────────────
        if edit_code:
            with db.get_session() as s:
                item = s.get(db.Item, edit_code)
                if item:
                    w_name.setText(item.item_name)
                    w_price.setValue(item.unit_price or 0.0)
                    # Non-graded qty = total minus sum of grade qtys
                    grade_qty_total = sum(g.quantity for g in item.grades)
                    non_graded_qty = max(0.0, (item.quantity_in_store or 0.0) - grade_qty_total)
                    w_qty.setValue(non_graded_qty)
                    if item.measurement_unit_id:
                        idx = w_unit.findData(item.measurement_unit_id)
                        if idx >= 0: w_unit.setCurrentIndex(idx)
                    w_sec_type.setText(item.section_type or "")
                    w_sec_code.setText(item.section_code or "")
                    w_location.setText(item.location or "")
                    w_remark.setPlainText(item.remark or "")
                    for fld, widget in [
                        ("section_size", w_sec_size), ("length", w_length),
                        ("scrap_length", w_scrap_len), ("width", w_width),
                        ("height", w_height), ("depth", w_depth),
                        ("thickness", w_thickness), ("weight", w_weight),
                        ("weight_in_tonne", w_wt_tonne), ("available_weight", w_avail_wt),
                        ("required_weight", w_req_wt), ("surface_area", w_surf_area),
                        ("cross_section_area", w_cross_area), ("area", w_area),
                        ("density", w_density),
                    ]:
                        v = getattr(item, fld, None)
                        if v is not None: widget.setValue(v)
                    if item.po_receipt_date:
                        w_po_date.setDate(QDate(item.po_receipt_date.year, item.po_receipt_date.month, item.po_receipt_date.day))
                    if item.last_date:
                        w_last_date.setDate(QDate(item.last_date.year, item.last_date.month, item.last_date.day))
                    for g in item.grades:
                        add_grade_row(g.grade, g.unit_price, g.quantity)
                    for isup in item.item_suppliers:
                        add_sup_row(isup.supplier_id, isup.quantity)

        # ── Bottom buttons ────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(20, 8, 20, 16)
        ok = QPushButton("Save Item"); ok.setObjectName("success")
        cancel = QPushButton("Cancel")
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(ok)
        root.addLayout(btn_row)

        def _qdate_to_py(qd):
            if qd == sentinel: return None
            return date(qd.year(), qd.month(), qd.day())

        def save():
            code = w_code.text().strip()
            name = w_name.text().strip()
            unit_id = w_unit.currentData()
            if not code or not name:
                QMessageBox.warning(dlg, "Validation", "Item Code and Name are required.")
                return
            if unit_id is None:
                QMessageBox.warning(dlg, "Validation", "Measurement Unit is required.")
                return

            grades_data = [
                (rw._grade_edit.text().strip(), rw._price_edit.value(), rw._qty_edit.value())
                for rw in grade_rows if rw._grade_edit.text().strip()
            ]
            sups_data = [
                (rw._sup_combo.currentData(), rw._qty_edit.value())
                for rw in sup_rows if rw._sup_combo.currentData()
            ]

            # Total qty = non-graded + sum of grade qtys + sum of supplier qtys
            non_graded_qty  = w_qty.value()
            grade_qty_total = sum(q for _, _, q in grades_data)
            sup_qty_total   = sum(q for _, q in sups_data)
            total_qty       = non_graded_qty + grade_qty_total + sup_qty_total

            with db.get_session() as s:
                if edit_code:
                    item = s.get(db.Item, edit_code)
                    for isup in list(item.item_suppliers): s.delete(isup)
                    for g    in list(item.grades):         s.delete(g)
                    s.flush()
                else:
                    item = db.Item(item_code=code,item_name=name)
                    s.add(item)
                    s.flush()

                item.item_name           = name
                item.unit_price          = w_price.value() or None
                item.measurement_unit_id = unit_id
                item.quantity_in_store   = total_qty
                item.section_type        = w_sec_type.text().strip() or None
                item.section_code        = w_sec_code.text().strip() or None
                item.location            = w_location.text().strip() or None
                item.remark              = w_remark.toPlainText().strip() or None
                item.last_update_by      = self.current_user.emp_id
                item.po_receipt_date     = _qdate_to_py(w_po_date.date())
                item.last_date           = _qdate_to_py(w_last_date.date())

                for fld, widget in [
                    ("section_size", w_sec_size), ("length", w_length),
                    ("scrap_length", w_scrap_len), ("width", w_width),
                    ("height", w_height), ("depth", w_depth),
                    ("thickness", w_thickness), ("weight", w_weight),
                    ("weight_in_tonne", w_wt_tonne), ("available_weight", w_avail_wt),
                    ("required_weight", w_req_wt), ("surface_area", w_surf_area),
                    ("cross_section_area", w_cross_area), ("area", w_area),
                    ("density", w_density),
                ]:
                    v = widget.value()
                    setattr(item, fld, v if v > 0 else None)

                for g, p, q in grades_data:
                    s.add(db.ItemGrade(item_code=item.item_code, grade=g, unit_price=p, quantity=q))

                for sid, qty in sups_data:
                    s.add(db.ItemSupplier(item_code=item.item_code, supplier_id=sid, quantity=qty))

                s.commit()

            self.refresh()
            dlg.accept()

        ok.clicked.connect(save)
        cancel.clicked.connect(dlg.reject)
        dlg.exec()

    def _add_dialog(self):   self._item_dialog()

    def _edit_dialog(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select an item to edit.")
            return
        self._item_dialog(edit_code=self.table.item(row, 0).text())

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0: return
        code = self.table.item(row, 0).text()
        name = self.table.item(row, 1).text()
        if QMessageBox.question(self, "Confirm", f"Delete item '{name}' ({code})?") == QMessageBox.StandardButton.Yes:
            with db.get_session() as s:
                obj = s.get(db.Item, code)
                if obj: s.delete(obj); s.commit()
            self.refresh()