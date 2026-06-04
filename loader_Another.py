"""Load items from Inventory_Record.xls into the inventory DB.

Each row can add stock to a different bucket for the same item code:
  - no supplier, no grade  -> non-supplier non-graded
  - no supplier, grade     -> item grade
  - supplier, no grade       -> supplier base qty
  - supplier, grade          -> supplier grade qty

Rows with the same item code are all processed (not skipped).
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inventory_app import db
from inventory_app.db import stock as inv_stock

db.init_db()

EXCEL_FILE = "Inventory_Record.xls"

# 0-based column indices (matches header row in the xls file)
COL = {
    "item_code": 1,
    "item": 2,
    "measurement_unit": 3,
    "grade": 4,
    "supplier": 5,
    "in_hand": 6,
    "unit_price": 8,
    "section_size": 9,
    "length": 10,
    "scrap_length": 11,
    "width": 12,
    "weight_in_tonne": 13,
    "available_weight": 14,
    "required_weight": 15,
    "surface_area": 16,
    "cross_section_area": 17,
    "depth": 18,
    "density": 19,
    "section_type": 21,
    "remark": 23,
    "thickness": 24,
    "height": 25,
    "section_code": 26,
    "weight": 27,
    "area": 28,
    "po_receipt_date": 29,
    "location": 30,
    "last_date": 31,
}


def clean_value(v):
    if pd.isna(v):
        return None
    s = str(v).strip()
    return s if s else None


def clean_float(v):
    if pd.isna(v):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def cell(row, key):
    return row.iloc[COL[key]]


def parse_date(v):
    if pd.isna(v):
        return None
    dt = pd.to_datetime(v, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.date()


def get_or_create_measurement_unit(session, name):
    if not name:
        return None
    mu = session.query(db.MeasurementUnit).filter_by(name=name).first()
    if not mu:
        mu = db.MeasurementUnit(name=name)
        session.add(mu)
        session.flush()
    return mu


def get_or_create_supplier(session, name):
    if not name:
        return None
    sup = session.query(db.Supplier).filter_by(name=name).first()
    if not sup:
        sup = db.Supplier(name=name)
        session.add(sup)
        session.flush()
    return sup


def build_item_fields(row):
    mu_name = clean_value(cell(row, "measurement_unit"))
    return {
        "item_name": clean_value(cell(row, "item")) or "",
        "unit_price": clean_float(cell(row, "unit_price")),
        "section_type": clean_value(cell(row, "section_type")),
        "section_code": clean_value(cell(row, "section_code")),
        "section_size": clean_float(cell(row, "section_size")),
        "length": clean_float(cell(row, "length")),
        "scrap_length": clean_float(cell(row, "scrap_length")),
        "width": clean_float(cell(row, "width")),
        "height": clean_float(cell(row, "height")),
        "depth": clean_float(cell(row, "depth")),
        "thickness": clean_float(cell(row, "thickness")),
        "weight": clean_float(cell(row, "weight")),
        "weight_in_tonne": clean_float(cell(row, "weight_in_tonne")),
        "available_weight": clean_float(cell(row, "available_weight")),
        "required_weight": clean_float(cell(row, "required_weight")),
        "surface_area": clean_float(cell(row, "surface_area")),
        "cross_section_area": clean_float(cell(row, "cross_section_area")),
        "area": clean_float(cell(row, "area")),
        "density": clean_float(cell(row, "density")),
        "location": clean_value(cell(row, "location")),
        "remark": clean_value(cell(row, "remark")),
        "po_receipt_date": parse_date(cell(row, "po_receipt_date")),
        "last_date": parse_date(cell(row, "last_date")),
        "_mu_name": mu_name,
    }


def get_or_create_item(session, item_code, row):
    item = session.query(db.Item).filter_by(item_code=item_code).first()
    if item:
        return item, False

    fields = build_item_fields(row)
    mu_name = fields.pop("_mu_name")
    item = db.Item(
        item_code=item_code,
        quantity_in_store=0.0,
        non_supplier_non_graded=0.0,
        measurement_unit=get_or_create_measurement_unit(session, mu_name),
        **fields,
    )
    session.add(item)
    session.flush()
    return item, True


def apply_row_stock(session, item, qty, price, supplier_id=None, grade=None):
    """Add qty to the correct bucket and set price on create."""
    inv_stock.add_stock(session, item, qty, supplier_id=supplier_id, grade=grade)

    if supplier_id:
        isup = inv_stock.get_item_supplier(session, item.item_code, supplier_id)
        if not isup:
            return
        if grade:
            sg = next((g for g in isup.grades if g.grade == grade), None)
            if sg and price is not None:
                sg.unit_price = price
        elif price is not None:
            isup.unit_price = price
    elif grade:
        g = session.query(db.ItemGrade).filter_by(
            item_code=item.item_code, grade=grade
        ).first()
        if g and price is not None:
            g.unit_price = price
    elif price is not None and item.unit_price is None:
        item.unit_price = price


def main():
    df = pd.read_html(EXCEL_FILE)[0].iloc[:, :33]
    data = df.iloc[1:].reset_index(drop=True)  # skip header row

    added_items = 0
    stock_rows = 0
    skipped_rows = 0

    for row_idx, row in data.iterrows():
        qty = clean_float(cell(row, "in_hand"))
        if qty is None:
            print(f"End of data at row {row_idx + 2} (In Hand empty).")
            break
        if qty <= 0:
            skipped_rows += 1
            continue

        item_code = clean_value(cell(row, "item_code"))
        if not item_code:
            skipped_rows += 1
            continue

        grade = clean_value(cell(row, "grade"))
        supplier_name = clean_value(cell(row, "supplier"))
        price = clean_float(cell(row, "unit_price"))

        with db.get_session() as s:
            item, created = get_or_create_item(s, item_code, row)
            if created:
                added_items += 1

            supplier = get_or_create_supplier(s, supplier_name)
            supplier_id = supplier.id if supplier else None

            apply_row_stock(
                s, item, qty, price,
                supplier_id=supplier_id,
                grade=grade,
            )
            s.commit()

            bucket = []
            if supplier_name:
                bucket.append(f"supplier={supplier_name}")
            if grade:
                bucket.append(f"grade={grade}")
            if not bucket:
                bucket.append("non-supplier/non-graded")
            stock_rows += 1
            print(
                f"{'Added' if created else 'Updated'} {item_code}: "
                f"+{qty} ({', '.join(bucket)})"
            )

    print(
        f"\nDone. New items: {added_items}, stock rows applied: {stock_rows}, "
        f"skipped (zero qty / no code): {skipped_rows}"
    )


if __name__ == "__main__":
    main()