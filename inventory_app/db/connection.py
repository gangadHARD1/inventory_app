from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "db_config.json")
DEFAULT_SQLITE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "inventory.db")
)


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    # Default: SQLite, no setup needed
    return {"dialect": "sqlite", "path": DEFAULT_SQLITE_PATH}


def save_config(config: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def build_url(config: dict) -> str:
    dialect = config.get("dialect", "sqlite")
    if dialect == "sqlite":
        path = config.get("path", DEFAULT_SQLITE_PATH)
        return f"sqlite:///{path}"
    else:
        return (
            f"postgresql+psycopg2://{config['user']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['dbname']}"
        )


_engine = None
_SessionLocal = None


def init_db(config: dict = None):
    global _engine, _SessionLocal
    if config is None:
        config = load_config()
    url = build_url(config)
    kwargs = {"connect_args": {"check_same_thread": False}} if config.get("dialect", "sqlite") == "sqlite" else {}
    _engine = create_engine(url, **kwargs)
    _SessionLocal = sessionmaker(bind=_engine)
    Base.metadata.create_all(_engine)
    _migrate_schema(_engine)


def _column_exists(conn, table: str, column: str) -> bool:
    if conn.dialect.name == "sqlite":
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        return any(r[1] == column for r in rows)
    r = conn.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).first()
    return r is not None


def _table_exists(conn, table: str) -> bool:
    if conn.dialect.name == "sqlite":
        r = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"),
            {"t": table},
        ).first()
        return r is not None
    r = conn.execute(
        text(
            "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
        ),
        {"t": table},
    ).first()
    return r is not None


def _migrate_schema(engine):
    with engine.begin() as conn:
        if _table_exists(conn, "item_suppliers") and not _column_exists(conn, "item_suppliers", "unit_price"):
            conn.execute(text("ALTER TABLE item_suppliers ADD COLUMN unit_price FLOAT"))
        if not _table_exists(conn, "item_supplier_grades"):
            Base.metadata.tables["item_supplier_grades"].create(conn)
        if _table_exists(conn, "items") and not _column_exists(conn, "items", "non_supplier_non_graded"):
            conn.execute(text("ALTER TABLE items ADD COLUMN non_supplier_non_graded FLOAT DEFAULT 0"))
            _backfill_non_supplier_non_graded(conn)


def _backfill_non_supplier_non_graded(conn):
    """Set non_supplier_non_graded from residual for existing rows."""
    rows = conn.execute(text("SELECT item_code, quantity_in_store FROM items")).fetchall()
    for item_code, total in rows:
        total = total or 0
        g_sum = conn.execute(
            text("SELECT COALESCE(SUM(quantity), 0) FROM item_grades WHERE item_code = :c"),
            {"c": item_code},
        ).scalar() or 0
        s_sum = conn.execute(
            text(
                "SELECT COALESCE(SUM("
                "  isup.quantity + COALESCE(("
                "    SELECT SUM(isg.quantity) FROM item_supplier_grades isg "
                "    WHERE isg.item_supplier_id = isup.id"
                "  ), 0)"
                "), 0) FROM item_suppliers isup WHERE isup.item_code = :c"
            ),
            {"c": item_code},
        ).scalar() or 0
        ng = max(0.0, total - g_sum - s_sum)
        conn.execute(
            text("UPDATE items SET non_supplier_non_graded = :ng WHERE item_code = :c"),
            {"ng": ng, "c": item_code},
        )


def get_session() -> Session:
    if _SessionLocal is None:
        init_db()
    session = _SessionLocal()
    session.__enter__ = lambda: session
    session.__exit__ = lambda *args: session.close()
    return session


def test_connection(config: dict) -> tuple[bool, str]:
    try:
        url = build_url(config)
        kwargs = {"connect_args": {"check_same_thread": False}} if config.get("dialect", "sqlite") == "sqlite" else {}
        engine = create_engine(url, **kwargs)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Connection successful!"
    except Exception as e:
        return False, str(e)
