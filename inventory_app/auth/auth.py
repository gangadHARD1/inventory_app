import hashlib
import os
from ..db import get_session, Employee, RolePermission

SUPERUSER_CATEGORIES = {"admin", "store manager"}


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split(":", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    except Exception:
        return False


def seed_admin():
    with get_session() as s:
        if s.query(Employee).count() == 0:
            admin = Employee(
                emp_id="admin", first_name="Admin", last_name="User",
                category="admin", hashed_password=hash_password("admin123"),
                must_change_password=True, is_active=True,
            )
            s.add(admin)
            s.commit()


def authenticate(emp_id: str, password: str):
    with get_session() as s:
        emp = s.query(Employee).filter_by(emp_id=emp_id, is_active=True).first()
        if not emp:
            return None, "Invalid Employee ID"
        if emp.hashed_password is None:
            return emp, "first_login"
        if not verify_password(password, emp.hashed_password):
            return None, "Incorrect password"
        return emp, None


def is_superuser(category: str) -> bool:
    return (category or "").lower() in SUPERUSER_CATEGORIES


def can(category: str, table: str, action: str) -> bool:
    """
    action: view | add | edit | delete | create_employee | adhoc_issue
    Superusers always pass.
    """
    if is_superuser(category):
        return True
    with get_session() as s:
        p = s.query(RolePermission).filter_by(category=category, table_name=table).first()
        if not p:
            return False
        return {
            "view":            p.can_view,
            "add":             p.can_add,
            "edit":            p.can_edit,
            "delete":          p.can_delete,
            "create_employee": p.can_create_employee,
            "adhoc_issue":     p.can_adhoc_issue,
        }.get(action, False)