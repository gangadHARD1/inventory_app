from sqlalchemy import (
    Column, String, Integer, Float, Date, DateTime, ForeignKey,
    Table, Boolean, UniqueConstraint, Text
)
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


# ── Many-to-many ──────────────────────────────────────────────────────────────
work_order_contractors = Table(
    "work_order_contractors", Base.metadata,
    Column("work_order_id", Integer, ForeignKey("work_orders.id"), primary_key=True),
    Column("contractor_id", Integer, ForeignKey("contractors.id"), primary_key=True),
)
work_order_customers = Table(
    "work_order_customers", Base.metadata,
    Column("work_order_id", Integer, ForeignKey("work_orders.id"), primary_key=True),
    Column("customer_id",   Integer, ForeignKey("customers.id"),  primary_key=True),
)
item_class_groups = Table(
    "item_class_groups", Base.metadata,
    Column("item_class_id", Integer, ForeignKey("item_classes.id"),  primary_key=True),
    Column("item_group_id", Integer, ForeignKey("item_groups.id"),   primary_key=True),
)


# ── Auth / Permissions ────────────────────────────────────────────────────────
class Employee(Base):
    __tablename__ = "employees"
    emp_id               = Column(String(100), primary_key=True)
    first_name           = Column(String(100), nullable=False)
    last_name            = Column(String(100), nullable=False)
    dob                  = Column(Date,        nullable=True)
    category             = Column(String(100), nullable=True)
    hashed_password      = Column(String(255), nullable=True)
    must_change_password = Column(Boolean,     default=True)
    is_active            = Column(Boolean,     default=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    id                  = Column(Integer,      primary_key=True, autoincrement=True)
    category            = Column(String(100),  nullable=False)
    table_name          = Column(String(100),  nullable=False)
    can_view            = Column(Boolean,      default=False)
    can_add             = Column(Boolean,      default=False)
    can_edit            = Column(Boolean,      default=False)
    can_delete          = Column(Boolean,      default=False)
    can_create_employee = Column(Boolean,      default=False)
    can_adhoc_issue     = Column(Boolean,      default=False)
    __table_args__ = (UniqueConstraint("category", "table_name"),)


# ── Lookup tables ─────────────────────────────────────────────────────────────
class MeasurementUnit(Base):
    __tablename__ = "measurement_units"
    id   = Column(Integer,     primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True,       nullable=False)


class ItemGroup(Base):
    __tablename__ = "item_groups"
    id   = Column(Integer,     primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True,       nullable=False)
    item_classes = relationship("ItemClass", secondary=item_class_groups, back_populates="item_groups")


class ItemClass(Base):
    __tablename__ = "item_classes"
    id          = Column(Integer,     primary_key=True, autoincrement=True)
    name        = Column(String(255), unique=True,       nullable=False)
    item_groups = relationship("ItemGroup", secondary=item_class_groups, back_populates="item_classes")


class Contractor(Base):
    __tablename__ = "contractors"
    id   = Column(Integer,     primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True,       nullable=False)


class Customer(Base):
    __tablename__ = "customers"
    id   = Column(Integer,     primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True,       nullable=False)


class Supplier(Base):
    __tablename__ = "suppliers"
    id   = Column(Integer,     primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True,       nullable=False)


class WorkOrderCategory(Base):
    __tablename__ = "work_order_categories"
    id   = Column(Integer,     primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True,       nullable=False)


class WorkOrder(Base):
    __tablename__ = "work_orders"
    id          = Column(Integer,     primary_key=True, autoincrement=True)
    name        = Column(String(255), unique=True,       nullable=False)
    category_id = Column(Integer,     ForeignKey("work_order_categories.id"), nullable=True)
    category    = relationship("WorkOrderCategory")
    contractors = relationship("Contractor", secondary=work_order_contractors)
    customers   = relationship("Customer",   secondary=work_order_customers)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id   = Column(Integer,     primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True,       nullable=False)


# ── Items ─────────────────────────────────────────────────────────────────────
class ItemGrade(Base):
    __tablename__ = "item_grades"
    id         = Column(Integer,     primary_key=True, autoincrement=True)
    item_code  = Column(String(100), ForeignKey("items.item_code"), nullable=False)
    grade      = Column(String(100), nullable=False)
    unit_price = Column(Float,       nullable=False)
    quantity   = Column(Float,       default=0.0, nullable=False)
    item       = relationship("Item", back_populates="grades")


class ItemSupplier(Base):
    """Per-supplier stock for an item: base (non-graded) qty/price plus optional grades."""
    __tablename__ = "item_suppliers"
    id          = Column(Integer,     primary_key=True, autoincrement=True)
    item_code   = Column(String(100), ForeignKey("items.item_code"), nullable=False)
    supplier_id = Column(Integer,     ForeignKey("suppliers.id"),    nullable=False)
    unit_price  = Column(Float,       nullable=True)
    quantity    = Column(Float,       default=0.0, nullable=False)
    item        = relationship("Item", back_populates="item_suppliers")
    supplier    = relationship("Supplier")
    grades      = relationship(
        "ItemSupplierGrade", back_populates="item_supplier", cascade="all, delete-orphan"
    )
    __table_args__ = (UniqueConstraint("item_code", "supplier_id"),)


class ItemSupplierGrade(Base):
    __tablename__ = "item_supplier_grades"
    id               = Column(Integer,     primary_key=True, autoincrement=True)
    item_supplier_id = Column(Integer,     ForeignKey("item_suppliers.id"), nullable=False)
    grade            = Column(String(100), nullable=False)
    unit_price       = Column(Float,       nullable=False)
    quantity         = Column(Float,       default=0.0, nullable=False)
    item_supplier    = relationship("ItemSupplier", back_populates="grades")
    __table_args__ = (UniqueConstraint("item_supplier_id", "grade"),)


class Item(Base):
    __tablename__ = "items"
    item_code           = Column(String(100), primary_key=True)
    item_name           = Column(String(255), nullable=False)
    unit_price          = Column(Float,       nullable=True)
    quantity_in_store   = Column(Float,       default=0.0)
    non_supplier_non_graded = Column(Float,   default=0.0)
    measurement_unit_id = Column(Integer,     ForeignKey("measurement_units.id"), nullable=True)
    measurement_unit    = relationship("MeasurementUnit")
    section_type        = Column(String(100), nullable=True)
    section_code        = Column(String(100), nullable=True)
    section_size        = Column(Float,       nullable=True)
    length              = Column(Float,       nullable=True)
    scrap_length        = Column(Float,       nullable=True)
    width               = Column(Float,       nullable=True)
    height              = Column(Float,       nullable=True)
    depth               = Column(Float,       nullable=True)
    thickness           = Column(Float,       nullable=True)
    weight              = Column(Float,       nullable=True)
    weight_in_tonne     = Column(Float,       nullable=True)
    available_weight    = Column(Float,       nullable=True)
    required_weight     = Column(Float,       nullable=True)
    surface_area        = Column(Float,       nullable=True)
    cross_section_area  = Column(Float,       nullable=True)
    area                = Column(Float,       nullable=True)
    density             = Column(Float,       nullable=True)
    location            = Column(String(255), nullable=True)
    remark              = Column(Text,        nullable=True)
    po_receipt_date     = Column(Date,        nullable=True)
    last_date           = Column(Date,        nullable=True)
    last_update_by      = Column(String(100), nullable=True)
    grades         = relationship("ItemGrade",    back_populates="item", cascade="all, delete-orphan")
    item_suppliers = relationship("ItemSupplier", back_populates="item", cascade="all, delete-orphan")


# ── Issues ────────────────────────────────────────────────────────────────────
class Issue(Base):
    __tablename__ = "issues"
    id              = Column(Integer,   primary_key=True, autoincrement=True)
    timestamp       = Column(DateTime,  default=datetime.now)
    issue_date      = Column(Date,      nullable=False)
    is_adhoc        = Column(Boolean,   default=False)
    item_code       = Column(String(100), ForeignKey("items.item_code"), nullable=False)
    item_name       = Column(String(255), nullable=False)
    grade           = Column(String(100), nullable=True)
    quantity_issued = Column(Float,     nullable=False)
    unit_price      = Column(Float,     nullable=False)
    total_value     = Column(Float,     nullable=False)
    item_class_id   = Column(Integer,   ForeignKey("item_classes.id"), nullable=True)
    item_class_name = Column(String(255), nullable=True)
    item_group_name = Column(String(255), nullable=True)
    supplier_id     = Column(Integer,   ForeignKey("suppliers.id"),    nullable=True)
    supplier_name   = Column(String(255), nullable=True)
    supplier_linked = Column(Boolean,   default=False)
    work_order_id   = Column(Integer,   ForeignKey("work_orders.id"),  nullable=True)
    work_order_name = Column(String(255), nullable=True)
    contractor_id   = Column(Integer,   ForeignKey("contractors.id"),  nullable=True)
    contractor_name = Column(String(255), nullable=True)
    customer_id     = Column(Integer,   ForeignKey("customers.id"),    nullable=True)
    customer_name   = Column(String(255), nullable=True)
    submitted_by    = Column(String(100), ForeignKey("employees.emp_id"), nullable=True)
    item       = relationship("Item")
    item_class = relationship("ItemClass")
    supplier   = relationship("Supplier")
    work_order = relationship("WorkOrder")
    contractor = relationship("Contractor")
    customer   = relationship("Customer")


# ── Receivables ───────────────────────────────────────────────────────────────
RECEIVABLE_STATUSES = ["Ordered", "In Inspection", "Approved"]


class Receivable(Base):
    __tablename__ = "receivables"
    id               = Column(Integer,     primary_key=True, autoincrement=True)
    timestamp        = Column(DateTime,    default=datetime.now)
    purchase_order_id= Column(Integer,     ForeignKey("purchase_orders.id"), nullable=False)
    supplier_id      = Column(Integer,     ForeignKey("suppliers.id"),        nullable=True)
    status           = Column(String(50),  default="Ordered", nullable=False)
    submitted_by     = Column(String(100), ForeignKey("employees.emp_id"),    nullable=True)
    has_failures     = Column(Boolean,     default=False)   # True once any item failed
    purchase_order   = relationship("PurchaseOrder")
    supplier         = relationship("Supplier")
    items            = relationship("ReceivableItem", back_populates="receivable",
                                   cascade="all, delete-orphan")


class ReceivableItem(Base):
    """One line item inside a receivable."""
    __tablename__ = "receivable_items"
    id            = Column(Integer,     primary_key=True, autoincrement=True)
    receivable_id = Column(Integer,     ForeignKey("receivables.id"), nullable=False)
    item_code     = Column(String(100), ForeignKey("items.item_code"), nullable=False)
    item_name     = Column(String(255), nullable=False)
    grade         = Column(String(100), nullable=True)
    quantity      = Column(Float,       nullable=False)
    # Inspection results (filled during status change)
    qty_passed    = Column(Float,       default=0.0)
    qty_failed    = Column(Float,       default=0.0)
    receivable    = relationship("Receivable", back_populates="items")
    item          = relationship("Item")


class FastMovablesCache(Base):
    __tablename__ = "fast_movables_cache"
    id          = Column(Integer,  primary_key=True, autoincrement=True)
    computed_on = Column(DateTime, nullable=False)
    week_start  = Column(Date,     nullable=False)
    item_code   = Column(String(100), nullable=False)
    item_name   = Column(String(255), nullable=False)
    total_qty   = Column(Float,    nullable=False)
    rank        = Column(Integer,  nullable=False)