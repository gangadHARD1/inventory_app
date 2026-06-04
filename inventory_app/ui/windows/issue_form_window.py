from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QDoubleSpinBox, QDateEdit, QFrame,
    QMessageBox, QScrollArea, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, QDate, Signal
from ...utils.widgets import make_label, make_separator, SearchableComboBox
from ... import db
from ...db import stock as inv_stock
from ...auth.auth import can as auth_can, is_superuser
from datetime import date, datetime


class IssueFormWindow(QWidget):
    issue_submitted = Signal()

    def __init__(self, current_user, parent=None):
        self.current_user = current_user
        super().__init__(parent)
        self.setWindowTitle("New Issue")
        self.resize(700, 920)
        self._selected_item = None
        self._effective_price = None
        self._supplier_ctx_set = False
        self._can_adhoc = (
            auth_can(self.current_user.category, "issues", "adhoc_issue")
            or is_superuser(self.current_user.category)
        )
        self._build_ui()
        self._load_dropdowns()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_dropdowns()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        top = QFrame()
        top.setObjectName("top_bar")
        top.setFixedHeight(64)
        tl = QHBoxLayout(top)
        tl.setContentsMargins(24, 0, 24, 0)
        title_lbl = QLabel("New Issue")
        title_lbl.setObjectName("title")
        tl.addWidget(title_lbl)
        tl.addStretch()
        if self._can_adhoc:
            self.adhoc_cb = QCheckBox("Ad-hoc Issue (allow zero stock)")
            self.adhoc_cb.setStyleSheet("color:#f59e0b; font-weight:600;")
            tl.addWidget(self.adhoc_cb)
        else:
            self.adhoc_cb = None
        outer.addWidget(top)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(28, 20, 28, 20)
        bl.setSpacing(20)

        item_grp = QGroupBox("ITEM DETAILS")
        igl = QVBoxLayout(item_grp)
        igl.setSpacing(12)

        igl.addWidget(make_label("Item  (search by name)"))
        self.item_search = SearchableComboBox("Type item name...")
        self.item_search.selectionChanged.connect(self._on_item_selected)
        igl.addWidget(self.item_search)

        code_row = QHBoxLayout()
        code_row.addWidget(make_label("Item Code:"))
        self.lbl_item_code = QLabel("—")
        self.lbl_item_code.setStyleSheet("color:#38bdf8; font-weight:600;")
        code_row.addWidget(self.lbl_item_code)
        code_row.addStretch()
        igl.addLayout(code_row)

        totals_row = QHBoxLayout()
        totals_row.addWidget(make_label("Non-supplier total:"))
        self.lbl_non_sup_total = QLabel("—")
        self.lbl_non_sup_total.setStyleSheet("color:#4ade80; font-weight:600;")
        totals_row.addWidget(self.lbl_non_sup_total)
        totals_row.addSpacing(20)
        totals_row.addWidget(make_label("Supplier total:"))
        self.lbl_sup_total = QLabel("—")
        self.lbl_sup_total.setStyleSheet("color:#a78bfa; font-weight:600;")
        totals_row.addWidget(self.lbl_sup_total)
        totals_row.addStretch()
        igl.addLayout(totals_row)

        grand_row = QHBoxLayout()
        grand_row.addWidget(make_label("Grand total in store:"))
        self.lbl_grand_total = QLabel("—")
        self.lbl_grand_total.setStyleSheet("color:#f1f5f9; font-weight:600;")
        grand_row.addWidget(self.lbl_grand_total)
        grand_row.addStretch()
        igl.addLayout(grand_row)

        self.grade_label = make_label("Grade")
        self.grade_combo = QComboBox()
        self.grade_combo.addItem("— No Grade —", None)
        self.grade_combo.currentIndexChanged.connect(self._on_grade_changed)
        self.grade_label.setVisible(False)
        self.grade_combo.setVisible(False)
        igl.addWidget(self.grade_label)
        igl.addWidget(self.grade_combo)

        avail_row = QHBoxLayout()
        self.lbl_avail_label = make_label("Available (this selection):")
        self.lbl_avail_qty = QLabel("—")
        self.lbl_avail_qty.setStyleSheet("color:#38bdf8; font-weight:600;")
        avail_row.addWidget(self.lbl_avail_label)
        avail_row.addWidget(self.lbl_avail_qty)
        avail_row.addStretch()
        self.lbl_avail_label.setVisible(False)
        self.lbl_avail_qty.setVisible(False)
        igl.addLayout(avail_row)

        price_row = QHBoxLayout()
        price_row.addWidget(make_label("Unit Price:"))
        self.lbl_unit_price = QLabel("₹ 0.00")
        self.lbl_unit_price.setStyleSheet("color:#4ade80; font-weight:600; font-size:14px;")
        price_row.addWidget(self.lbl_unit_price)
        price_row.addStretch()
        igl.addLayout(price_row)

        igl.addWidget(make_label("Quantity Issued"))
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.01, 9999999)
        self.qty_spin.setDecimals(2)
        self.qty_spin.setValue(1.0)
        self.qty_spin.valueChanged.connect(self._update_total)
        igl.addWidget(self.qty_spin)

        total_row = QHBoxLayout()
        total_row.addWidget(make_label("Total Value:"))
        self.lbl_total = QLabel("₹ 0.00")
        self.lbl_total.setStyleSheet("color:#f59e0b; font-weight:700; font-size:15px;")
        total_row.addWidget(self.lbl_total)
        total_row.addStretch()
        igl.addLayout(total_row)
        bl.addWidget(item_grp)

        sup_grp = QGroupBox("SUPPLIER")
        sgl = QVBoxLayout(sup_grp)
        sgl.setSpacing(10)
        self.sup_mode_cb = QCheckBox("Pick from item's linked suppliers only")
        self.sup_mode_cb.setChecked(True)
        self.sup_mode_cb.stateChanged.connect(self._refresh_supplier_list)
        sgl.addWidget(self.sup_mode_cb)
        sgl.addWidget(make_label("Supplier  (optional — leave blank for non-supplier stock)"))
        self.supplier_combo = QComboBox()
        self.supplier_combo.currentIndexChanged.connect(self._on_supplier_changed)
        sgl.addWidget(self.supplier_combo)
        bl.addWidget(sup_grp)

        class_grp = QGroupBox("CLASSIFICATION")
        cgl = QVBoxLayout(class_grp)
        cgl.setSpacing(10)
        cgl.addWidget(make_label("Item Class"))
        self.item_class_combo = QComboBox()
        self.item_class_combo.addItem("— Select Item Class —", None)
        self.item_class_combo.currentIndexChanged.connect(self._on_class_changed)
        cgl.addWidget(self.item_class_combo)
        cgl.addWidget(make_label("Item Group"))
        self.item_group_combo = QComboBox()
        self.item_group_combo.addItem("— Select Item Group —", None)
        cgl.addWidget(self.item_group_combo)
        bl.addWidget(class_grp)

        date_grp = QGroupBox("ISSUE DATE")
        dgl = QVBoxLayout(date_grp)
        dgl.setSpacing(8)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd MMM yyyy")
        dgl.addWidget(self.date_edit)
        bl.addWidget(date_grp)

        wo_grp = QGroupBox("WORK ORDER  (optional)")
        wgl = QVBoxLayout(wo_grp)
        wgl.setSpacing(10)
        wgl.addWidget(make_label("Work Order"))
        self.wo_combo = QComboBox()
        self.wo_combo.addItem("— None —", None)
        self.wo_combo.currentIndexChanged.connect(self._on_wo_changed)
        wgl.addWidget(self.wo_combo)
        wgl.addWidget(make_label("Contractor"))
        self.contractor_combo = QComboBox()
        self.contractor_combo.addItem("— None —", None)
        wgl.addWidget(self.contractor_combo)
        wgl.addWidget(make_label("Customer"))
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("— None —", None)
        wgl.addWidget(self.customer_combo)
        bl.addWidget(wo_grp)

        bl.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll)

        bottom = QFrame()
        bottom.setObjectName("top_bar")
        bottom.setFixedHeight(64)
        btm_l = QHBoxLayout(bottom)
        btm_l.setContentsMargins(24, 0, 24, 0)
        btm_l.addStretch()
        self.btn_reset = QPushButton("↺  Reset")
        self.btn_reset.setFixedWidth(110)
        self.btn_submit = QPushButton("✓  Submit Issue")
        self.btn_submit.setObjectName("success")
        self.btn_submit.setFixedWidth(160)
        btm_l.addWidget(self.btn_reset)
        btm_l.addWidget(self.btn_submit)
        outer.addWidget(bottom)

        self.btn_reset.clicked.connect(self._reset_form)
        self.btn_submit.clicked.connect(self._submit)

    def _build_item_payload(self, item):
        suppliers = {}
        for isup in item.item_suppliers:
            suppliers[isup.supplier_id] = {
                "name": isup.supplier.name,
                "base_price": isup.unit_price,
                "base_qty": isup.quantity or 0,
                "grades": {
                    sg.grade: {"price": sg.unit_price, "qty": sg.quantity or 0}
                    for sg in isup.grades
                },
            }
        item_grades = {
            g.grade: {"price": g.unit_price, "qty": g.quantity or 0}
            for g in item.grades
        }
        non_sup = inv_stock.non_supplier_total_qty(item)
        sup_tot = inv_stock.all_supplier_stock_qty(item)
        return {
            "code": item.item_code,
            "name": item.item_name,
            "base_price": item.unit_price,
            "item_grades": item_grades,
            "suppliers": suppliers,
            "non_supplier_total": non_sup,
            "supplier_total": sup_tot,
            "grand_total": item.quantity_in_store or 0,
            "non_supplier_non_graded": inv_stock.non_supplier_non_graded_qty(item),
        }

    def _load_dropdowns(self):
        with db.get_session() as s:
            from sqlalchemy.orm import joinedload

            items = (
                s.query(db.Item)
                .options(
                    joinedload(db.Item.grades),
                    joinedload(db.Item.item_suppliers).joinedload(db.ItemSupplier.supplier),
                    joinedload(db.Item.item_suppliers).joinedload(db.ItemSupplier.grades),
                )
                .order_by(db.Item.item_name)
                .all()
            )
            item_list = [
                (f"{item.item_name}  [{item.item_code}]", self._build_item_payload(item))
                for item in items
            ]

            classes = (
                s.query(db.ItemClass)
                .options(joinedload(db.ItemClass.item_groups))
                .order_by(db.ItemClass.name)
                .all()
            )
            class_list = [
                (ic.name, {"id": ic.id, "name": ic.name, "groups": [g.name for g in ic.item_groups]})
                for ic in classes
            ]
            work_orders = [
                (wo.name, wo.id) for wo in s.query(db.WorkOrder).order_by(db.WorkOrder.name).all()
            ]

        self.item_search.set_items(item_list)
        for name, data in class_list:
            self.item_class_combo.addItem(name, data)
        for name, wo_id in work_orders:
            self.wo_combo.addItem(name, wo_id)
        self._refresh_supplier_list()

    def _on_item_selected(self, data):
        self._selected_item = data
        self._supplier_ctx_set = False
        self._hide_grade_ui()

        if data is None:
            self.lbl_item_code.setText("—")
            self.lbl_non_sup_total.setText("—")
            self.lbl_sup_total.setText("—")
            self.lbl_grand_total.setText("—")
            self._effective_price = None
            self.lbl_unit_price.setText("₹ 0.00")
            self._update_total()
            self._refresh_supplier_list()
            return

        self.lbl_item_code.setText(data["code"])
        self.lbl_non_sup_total.setText(f"{data['non_supplier_total']:,.2f}")
        self.lbl_sup_total.setText(f"{data['supplier_total']:,.2f}")
        self.lbl_grand_total.setText(f"{data['grand_total']:,.2f}")
        self._refresh_supplier_list()
        self.supplier_combo.blockSignals(True)
        self.supplier_combo.setCurrentIndex(0)
        self.supplier_combo.blockSignals(False)
        self._on_supplier_changed()

    def _hide_grade_ui(self):
        self.grade_label.setVisible(False)
        self.grade_combo.setVisible(False)
        self.lbl_avail_label.setVisible(False)
        self.lbl_avail_qty.setVisible(False)

    def _refresh_grade_combo(self):
        data = self._selected_item
        if not data:
            return

        sup_id = self.supplier_combo.currentData()
        self.grade_combo.blockSignals(True)
        self.grade_combo.clear()
        self.grade_combo.addItem("— No Grade —", None)

        if sup_id and sup_id in data["suppliers"]:
            sup = data["suppliers"][sup_id]
            for g, info in sup["grades"].items():
                if info["qty"] > 0:
                    self.grade_combo.addItem(g, g)
            has_grades = any(info["qty"] > 0 for info in sup["grades"].values())
        else:
            for g, info in data["item_grades"].items():
                if info["qty"] > 0:
                    self.grade_combo.addItem(g, g)
            has_grades = any(info["qty"] > 0 for info in data["item_grades"].values())

        self.grade_combo.blockSignals(False)
        self.grade_label.setVisible(has_grades)
        self.grade_combo.setVisible(has_grades)

    def _context_avail_and_price(self):
        data = self._selected_item
        if not data:
            return 0.0, 0.0

        sup_id = self.supplier_combo.currentData()
        grade = self.grade_combo.currentData()

        if sup_id and sup_id in data["suppliers"]:
            sup = data["suppliers"][sup_id]
            if grade and grade in sup["grades"]:
                g = sup["grades"][grade]
                return g["qty"], g["price"]
            return sup["base_qty"], sup["base_price"] or data.get("base_price") or 0

        if grade and grade in data["item_grades"]:
            g = data["item_grades"][grade]
            return g["qty"], g["price"]
        return data["non_supplier_non_graded"], data.get("base_price") or 0

    def _on_supplier_changed(self):
        if not self._selected_item:
            self._hide_grade_ui()
            return

        self._supplier_ctx_set = True
        self._refresh_grade_combo()
        self.lbl_avail_label.setVisible(True)
        self.lbl_avail_qty.setVisible(True)
        self._on_grade_changed()

    def _on_grade_changed(self):
        if not self._selected_item or not self._supplier_ctx_set:
            return
        avail, price = self._context_avail_and_price()
        self.lbl_avail_qty.setText(f"{avail:,.2f}")
        self._effective_price = price
        self.lbl_unit_price.setText(f"₹ {price:,.2f}")
        self._update_total()

    def _update_total(self):
        price = self._effective_price or 0
        self.lbl_total.setText(f"₹ {price * self.qty_spin.value():,.2f}")

    def _on_class_changed(self):
        ic_data = self.item_class_combo.currentData()
        self.item_group_combo.clear()
        self.item_group_combo.addItem("— Select Item Group —", None)
        if ic_data:
            for g in ic_data["groups"]:
                self.item_group_combo.addItem(g, g)
            if len(ic_data["groups"]) == 1:
                self.item_group_combo.setCurrentIndex(1)

    def _refresh_supplier_list(self):
        self.supplier_combo.blockSignals(True)
        self.supplier_combo.clear()
        self.supplier_combo.addItem("— None (non-supplier stock) —", None)
        linked_only = self.sup_mode_cb.isChecked()
        if self._selected_item:
            if linked_only:
                for sid, sup in self._selected_item["suppliers"].items():
                    tot = sup["base_qty"] + sum(g["qty"] for g in sup["grades"].values())
                    self.supplier_combo.addItem(f"{sup['name']}  (qty: {tot:,.2f})", sid)
            elif not linked_only:
                with db.get_session() as s:
                    for sup in s.query(db.Supplier).order_by(db.Supplier.name).all():
                        self.supplier_combo.addItem(sup.name, sup.id)
        self.supplier_combo.blockSignals(False)
        if self._selected_item:
            self._on_supplier_changed()

    def _on_wo_changed(self):
        wo_id = self.wo_combo.currentData()
        self.contractor_combo.clear()
        self.customer_combo.clear()
        self.contractor_combo.addItem("— None —", None)
        self.customer_combo.addItem("— None —", None)
        if wo_id is None:
            with db.get_session() as s:
                for c in s.query(db.Contractor).order_by(db.Contractor.name).all():
                    self.contractor_combo.addItem(c.name, c.id)
                for c in s.query(db.Customer).order_by(db.Customer.name).all():
                    self.customer_combo.addItem(c.name, c.id)
            return
        with db.get_session() as s:
            wo = s.get(db.WorkOrder, wo_id)
            if wo:
                for c in wo.contractors:
                    self.contractor_combo.addItem(c.name, c.id)
                for c in wo.customers:
                    self.customer_combo.addItem(c.name, c.id)
                if len(wo.contractors) == 1:
                    self.contractor_combo.setCurrentIndex(1)
                if len(wo.customers) == 1:
                    self.customer_combo.setCurrentIndex(1)

    def _reset_form(self):
        self.item_search.clear_selection()
        self.grade_combo.clear()
        self.grade_combo.addItem("— No Grade —", None)
        self._hide_grade_ui()
        self.qty_spin.setValue(1.0)
        self.item_class_combo.setCurrentIndex(0)
        self.item_group_combo.clear()
        self.item_group_combo.addItem("— Select Item Group —", None)
        self.wo_combo.setCurrentIndex(0)
        self.date_edit.setDate(QDate.currentDate())
        self.lbl_item_code.setText("—")
        self.lbl_non_sup_total.setText("—")
        self.lbl_sup_total.setText("—")
        self.lbl_grand_total.setText("—")
        self.lbl_unit_price.setText("₹ 0.00")
        self.lbl_total.setText("₹ 0.00")
        self._selected_item = None
        self._effective_price = None
        self._supplier_ctx_set = False
        self._refresh_supplier_list()

    def _submit(self):
        is_adhoc = self.adhoc_cb.isChecked() if self.adhoc_cb else False

        if self._selected_item is None:
            QMessageBox.warning(self, "Validation", "Please select an item.")
            return
        if not self._supplier_ctx_set:
            QMessageBox.warning(self, "Validation", "Confirm supplier selection (or leave as None).")
            return

        price = self._effective_price or 0
        qty = self.qty_spin.value()
        total = price * qty
        grade = self.grade_combo.currentData()
        sup_id = self.supplier_combo.currentData()

        with db.get_session() as s:
            from sqlalchemy.orm import joinedload

            item = (
                s.query(db.Item)
                .options(
                    joinedload(db.Item.grades),
                    joinedload(db.Item.item_suppliers).joinedload(db.ItemSupplier.grades),
                )
                .filter_by(item_code=self._selected_item["code"])
                .first()
            )
            if not item:
                QMessageBox.critical(self, "Error", "Item not found.")
                return

            is_linked_supplier = bool(
                sup_id and inv_stock.get_item_supplier(s, item.item_code, sup_id)
            )
            avail = inv_stock.get_available_qty(s, item, sup_id, grade)

            if not is_adhoc and qty > avail:
                QMessageBox.warning(
                    self,
                    "Insufficient Stock",
                    f"Available: {avail:,.2f}\nRequested: {qty:,.2f}"
                    + ("\n\nEnable Ad-hoc Issue to proceed." if self._can_adhoc else ""),
                )
                return

        qd = self.date_edit.date()
        ic_data = self.item_class_combo.currentData()
        wo_id = self.wo_combo.currentData()
        cont_id = self.contractor_combo.currentData()
        cust_id = self.customer_combo.currentData()
        ig_name = self.item_group_combo.currentData()

        with db.get_session() as s:
            item = s.get(db.Item, self._selected_item["code"])
            sup_name = None
            if sup_id:
                sup = s.get(db.Supplier, sup_id)
                sup_name = sup.name if sup else None

            issue = db.Issue(
                issue_date=date(qd.year(), qd.month(), qd.day()),
                timestamp=datetime.now(),
                is_adhoc=is_adhoc,
                item_code=item.item_code,
                item_name=item.item_name,
                grade=grade,
                quantity_issued=qty,
                unit_price=price,
                total_value=total,
                item_class_id=ic_data["id"] if ic_data else None,
                item_class_name=ic_data["name"] if ic_data else None,
                item_group_name=ig_name,
                supplier_id=sup_id,
                supplier_name=sup_name,
                supplier_linked=is_linked_supplier,
                work_order_id=wo_id,
                work_order_name=self.wo_combo.currentText() if wo_id else None,
                contractor_id=cont_id,
                contractor_name=self.contractor_combo.currentText() if cont_id else None,
                customer_id=cust_id,
                customer_name=self.customer_combo.currentText() if cust_id else None,
                submitted_by=self.current_user.emp_id,
            )
            s.add(issue)
            inv_stock.deduct_stock(s, item, qty, sup_id, grade)
            s.commit()

        adhoc_note = " (Ad-hoc)" if is_adhoc else ""
        QMessageBox.information(
            self,
            "Success",
            f"Issue submitted{adhoc_note}!\n\nItem: {self._selected_item['name']}\n"
            f"Qty: {qty}  ×  ₹{price:,.2f}  =  ₹{total:,.2f}",
        )
        self._reset_form()
        self.issue_submitted.emit()
