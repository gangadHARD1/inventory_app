from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QDoubleSpinBox, QFrame, QMessageBox,
    QScrollArea, QGroupBox, QFormLayout
)
from PySide6.QtCore import Signal
from ...utils.widgets import make_label, make_separator
from ... import db
from datetime import datetime


class ReceivableItemRow(QWidget):
    def __init__(self, items_data, parent=None):
        super().__init__(parent)
        self._items_data = items_data
        self._supplier_id = None
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.item_combo = QComboBox()
        self.item_combo.setMinimumWidth(200)
        self.item_combo.addItem("— Select Item —", None)
        for d in self._items_data:
            self.item_combo.addItem(f"{d['name']} [{d['code']}]", d)
        self.item_combo.currentIndexChanged.connect(self._on_item_changed)

        self.grade_combo = QComboBox()
        self.grade_combo.setMinimumWidth(120)
        self.grade_combo.addItem("— No Grade —", None)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.01, 9999999)
        self.qty_spin.setDecimals(2)
        self.qty_spin.setValue(1.0)

        self.btn_remove = QPushButton("✕")
        self.btn_remove.setObjectName("icon_btn")
        self.btn_remove.setFixedWidth(28)

        layout.addWidget(self.item_combo, 3)
        layout.addWidget(self.grade_combo, 2)
        layout.addWidget(QLabel("Qty:"))
        layout.addWidget(self.qty_spin, 1)
        layout.addWidget(self.btn_remove)

    def set_supplier(self, supplier_id):
        self._supplier_id = supplier_id
        self._on_item_changed()

    def _grade_names_for_item(self, data):
        if not data:
            return []
        if self._supplier_id and self._supplier_id in data.get("supplier_grades", {}):
            return data["supplier_grades"][self._supplier_id]
        return data.get("item_grades", [])

    def _on_item_changed(self):
        data = self.item_combo.currentData()
        self.grade_combo.blockSignals(True)
        self.grade_combo.clear()
        self.grade_combo.addItem("— No Grade —", None)
        for g in self._grade_names_for_item(data):
            self.grade_combo.addItem(g, g)
        has = self.grade_combo.count() > 1
        self.grade_combo.setEnabled(has)
        self.grade_combo.blockSignals(False)

    def get_data(self):
        item_data = self.item_combo.currentData()
        if not item_data:
            return None
        return {
            "item_code": item_data["code"],
            "item_name": item_data["name"],
            "grade": self.grade_combo.currentData(),
            "quantity": self.qty_spin.value(),
        }


class ReceivableFormWindow(QWidget):
    receivable_submitted = Signal()

    def __init__(self, current_user, parent=None):
        self.current_user = current_user
        super().__init__(parent)
        self.setWindowTitle("New Receivable")
        self.resize(720, 640)
        self._item_rows = []
        self._items_data = []
        self._load_data()
        self._build_ui()

    def _load_data(self):
        with db.get_session() as s:
            from sqlalchemy.orm import joinedload

            self._pos = [
                (p.id, p.name) for p in s.query(db.PurchaseOrder).order_by(db.PurchaseOrder.name).all()
            ]
            self._suppliers = [
                (p.id, p.name) for p in s.query(db.Supplier).order_by(db.Supplier.name).all()
            ]
            items = (
                s.query(db.Item)
                .options(
                    joinedload(db.Item.grades),
                    joinedload(db.Item.item_suppliers).joinedload(db.ItemSupplier.grades),
                )
                .order_by(db.Item.item_name)
                .all()
            )
            self._items_data = []
            for i in items:
                supplier_grades = {}
                for isup in i.item_suppliers:
                    supplier_grades[isup.supplier_id] = [sg.grade for sg in isup.grades]
                self._items_data.append({
                    "code": i.item_code,
                    "name": i.item_name,
                    "item_grades": [g.grade for g in i.grades],
                    "supplier_grades": supplier_grades,
                })

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        top = QFrame()
        top.setObjectName("top_bar")
        top.setFixedHeight(64)
        tl = QHBoxLayout(top)
        tl.setContentsMargins(24, 0, 24, 0)
        title = QLabel("New Receivable")
        title.setObjectName("title")
        tl.addWidget(title)
        tl.addStretch()
        outer.addWidget(top)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(28, 20, 28, 20)
        bl.setSpacing(16)

        hdr_group = QGroupBox("RECEIVABLE DETAILS")
        hgl = QFormLayout(hdr_group)
        hgl.setSpacing(10)

        self.po_combo = QComboBox()
        self.po_combo.addItem("— Select PO * —", None)
        for po_id, po_name in self._pos:
            self.po_combo.addItem(po_name, po_id)

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("— None (item-level stock) —", None)
        for sup_id, sup_name in self._suppliers:
            self.supplier_combo.addItem(sup_name, sup_id)
        self.supplier_combo.currentIndexChanged.connect(self._on_supplier_changed)

        hgl.addRow(make_label("Purchase Order *"), self.po_combo)
        hgl.addRow(make_label("Supplier"), self.supplier_combo)
        bl.addWidget(hdr_group)

        items_group = QGroupBox("ITEMS")
        igl = QVBoxLayout(items_group)
        igl.setSpacing(8)

        col_hdr = QHBoxLayout()
        col_hdr.addWidget(QLabel("Item"), 3)
        col_hdr.addWidget(QLabel("Grade"), 2)
        col_hdr.addWidget(QLabel("Quantity"), 1)
        col_hdr.addWidget(QLabel(""), )
        igl.addLayout(col_hdr)
        igl.addWidget(make_separator())

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(4)
        igl.addWidget(self._rows_container)

        btn_add_row = QPushButton("＋  Add Item Row")
        btn_add_row.setObjectName("primary")
        btn_add_row.clicked.connect(self._add_item_row)
        igl.addWidget(btn_add_row)
        bl.addWidget(items_group)
        bl.addStretch()

        scroll.setWidget(body)
        outer.addWidget(scroll)

        bottom = QFrame()
        bottom.setObjectName("top_bar")
        bottom.setFixedHeight(64)
        btm_l = QHBoxLayout(bottom)
        btm_l.setContentsMargins(24, 0, 24, 0)
        btm_l.addStretch()
        btn_reset = QPushButton("↺  Reset")
        btn_reset.setFixedWidth(110)
        btn_submit = QPushButton("✓  Submit Receivable")
        btn_submit.setObjectName("success")
        btn_submit.setFixedWidth(180)
        btm_l.addWidget(btn_reset)
        btm_l.addWidget(btn_submit)
        outer.addWidget(bottom)

        btn_reset.clicked.connect(self._reset)
        btn_submit.clicked.connect(self._submit)
        self._add_item_row()

    def _on_supplier_changed(self):
        sup_id = self.supplier_combo.currentData()
        for row in self._item_rows:
            row.set_supplier(sup_id)

    def _add_item_row(self):
        row = ReceivableItemRow(self._items_data)
        row.set_supplier(self.supplier_combo.currentData())
        row.btn_remove.clicked.connect(lambda: self._remove_row(row))
        self._item_rows.append(row)
        self._rows_layout.addWidget(row)

    def _remove_row(self, row):
        if len(self._item_rows) <= 1:
            QMessageBox.information(self, "Info", "At least one item row is required.")
            return
        self._item_rows.remove(row)
        row.setParent(None)
        row.deleteLater()

    def _reset(self):
        self.po_combo.setCurrentIndex(0)
        self.supplier_combo.setCurrentIndex(0)
        for row in list(self._item_rows):
            row.setParent(None)
            row.deleteLater()
        self._item_rows.clear()
        self._add_item_row()

    def _submit(self):
        po_id = self.po_combo.currentData()
        if not po_id:
            QMessageBox.warning(self, "Validation", "Purchase Order is required.")
            return

        items_data = []
        for row in self._item_rows:
            d = row.get_data()
            if d:
                items_data.append(d)
        if not items_data:
            QMessageBox.warning(self, "Validation", "Add at least one item.")
            return

        sup_id = self.supplier_combo.currentData()

        with db.get_session() as s:
            rec = db.Receivable(
                purchase_order_id=po_id,
                supplier_id=sup_id,
                status="Ordered",
                submitted_by=self.current_user.emp_id,
                timestamp=datetime.now(),
            )
            s.add(rec)
            s.flush()
            for d in items_data:
                s.add(db.ReceivableItem(
                    receivable_id=rec.id,
                    item_code=d["item_code"],
                    item_name=d["item_name"],
                    grade=d["grade"],
                    quantity=d["quantity"],
                ))
            s.commit()
            rec_id = rec.id

        sup_note = ""
        if sup_id:
            sup_note = "\nStock will be added to this supplier when inspection passes."
        QMessageBox.information(
            self,
            "Success",
            f"Receivable #{rec_id} submitted with status 'Ordered'.{sup_note}",
        )
        self._reset()
        self.receivable_submitted.emit()
