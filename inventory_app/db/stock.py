"""Inventory quantity helpers (non-supplier vs supplier buckets)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from .models import Item, ItemGrade, ItemSupplier, ItemSupplierGrade


def supplier_graded_qty(isup: ItemSupplier) -> float:
    return sum((sg.quantity or 0) for sg in isup.grades)


def supplier_total_qty(isup: ItemSupplier) -> float:
    return (isup.quantity or 0) + supplier_graded_qty(isup)


def all_supplier_stock_qty(item: Item) -> float:
    return sum(supplier_total_qty(isup) for isup in item.item_suppliers)


def non_supplier_graded_qty(item: Item) -> float:
    return sum((g.quantity or 0) for g in item.grades)


def non_supplier_total_qty(item: Item) -> float:
    return non_supplier_non_graded_qty(item) + non_supplier_graded_qty(item)


def non_supplier_non_graded_qty(item: Item) -> float:
    stored = getattr(item, "non_supplier_non_graded", None)
    if stored is not None:
        return stored or 0.0
    total = item.quantity_in_store or 0
    return max(
        0.0,
        total - non_supplier_graded_qty(item) - all_supplier_stock_qty(item),
    )


def recompute_total_quantity(
    non_supplier_non_graded: float,
    item_grades: list[tuple],
    suppliers: list[tuple],
) -> float:
    """item_grades: [(grade, price, qty), ...]; suppliers: [(sid, base_price, base_qty, grade_rows), ...]"""
    g_total = sum(q for _, _, q in item_grades)
    s_total = 0.0
    for _sid, _bp, base_q, grade_rows in suppliers:
        s_total += base_q + sum(q for _, _, q in grade_rows)
    return non_supplier_non_graded + g_total + s_total


def get_item_supplier(session: Session, item_code: str, supplier_id: int) -> ItemSupplier | None:
    return session.query(ItemSupplier).filter_by(
        item_code=item_code, supplier_id=supplier_id
    ).first()


def get_available_qty(
    session: Session,
    item: Item,
    supplier_id: int | None = None,
    grade: str | None = None,
) -> float:
    if supplier_id:
        isup = get_item_supplier(session, item.item_code, supplier_id)
        if not isup:
            return 0.0
        if grade:
            sg = next((g for g in isup.grades if g.grade == grade), None)
            return sg.quantity if sg else 0.0
        return isup.quantity or 0.0
    if grade:
        g = session.query(ItemGrade).filter_by(item_code=item.item_code, grade=grade).first()
        return g.quantity if g else 0.0
    return non_supplier_non_graded_qty(item)


def resolve_unit_price(
    session: Session,
    item: Item,
    supplier_id: int | None = None,
    grade: str | None = None,
) -> float:
    if supplier_id:
        isup = get_item_supplier(session, item.item_code, supplier_id)
        if isup:
            if grade:
                sg = next((g for g in isup.grades if g.grade == grade), None)
                if sg:
                    return sg.unit_price
            if isup.unit_price is not None:
                return isup.unit_price
    if grade:
        g = session.query(ItemGrade).filter_by(item_code=item.item_code, grade=grade).first()
        if g:
            return g.unit_price
    return item.unit_price or 0.0


def deduct_stock(
    session: Session,
    item: Item,
    qty: float,
    supplier_id: int | None = None,
    grade: str | None = None,
) -> None:
    item.quantity_in_store = max(0.0, (item.quantity_in_store or 0) - qty)
    if supplier_id:
        isup = get_item_supplier(session, item.item_code, supplier_id)
        if not isup:
            return
        if grade:
            sg = next((g for g in isup.grades if g.grade == grade), None)
            if sg:
                sg.quantity = max(0.0, (sg.quantity or 0) - qty)
        else:
            isup.quantity = max(0.0, (isup.quantity or 0) - qty)
    elif grade:
        g = session.query(ItemGrade).filter_by(item_code=item.item_code, grade=grade).first()
        if g:
            g.quantity = max(0.0, (g.quantity or 0) - qty)
    else:
        item.non_supplier_non_graded = max(
            0.0, (getattr(item, "non_supplier_non_graded", None) or 0) - qty
        )


def add_stock(
    session: Session,
    item: Item,
    qty: float,
    supplier_id: int | None = None,
    grade: str | None = None,
) -> None:
    item.quantity_in_store = (item.quantity_in_store or 0) + qty
    if supplier_id:
        isup = get_item_supplier(session, item.item_code, supplier_id)
        if not isup:
            isup = ItemSupplier(
                item_code=item.item_code,
                supplier_id=supplier_id,
                quantity=0.0,
                unit_price=item.unit_price,
            )
            session.add(isup)
            session.flush()
        if grade:
            sg = next((g for g in isup.grades if g.grade == grade), None)
            if sg:
                sg.quantity = (sg.quantity or 0) + qty
            else:
                ref = session.query(ItemGrade).filter_by(
                    item_code=item.item_code, grade=grade
                ).first()
                price = ref.unit_price if ref else (isup.unit_price or item.unit_price or 0)
                session.add(ItemSupplierGrade(
                    item_supplier_id=isup.id,
                    grade=grade,
                    unit_price=price,
                    quantity=qty,
                ))
        else:
            isup.quantity = (isup.quantity or 0) + qty
    elif grade:
        g = session.query(ItemGrade).filter_by(item_code=item.item_code, grade=grade).first()
        if g:
            g.quantity = (g.quantity or 0) + qty
        else:
            session.add(ItemGrade(
                item_code=item.item_code,
                grade=grade,
                unit_price=item.unit_price or 0,
                quantity=qty,
            ))
    else:
        item.non_supplier_non_graded = (getattr(item, "non_supplier_non_graded", None) or 0) + qty
