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
