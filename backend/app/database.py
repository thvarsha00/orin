from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401  (registers tables)

    Base.metadata.create_all(bind=engine)
    _add_missing_columns()


def _add_missing_columns() -> None:
    """create_all never alters existing tables; add new columns to older SQLite files."""
    from sqlalchemy import inspect, text

    wanted = {
            "coding_problems": {
            "tags": "ALTER TABLE coding_problems ADD COLUMN tags JSON NOT NULL DEFAULT '[]'",
            "hints": "ALTER TABLE coding_problems ADD COLUMN hints JSON NOT NULL DEFAULT '[]'",
        },
        "profiles": {
            "preferred_script": "ALTER TABLE profiles ADD COLUMN preferred_script VARCHAR(10) NOT NULL DEFAULT 'auto'",
            "last_detected_script": "ALTER TABLE profiles ADD COLUMN last_detected_script VARCHAR(10)",
        },
        "documents": {
            "file_path": "ALTER TABLE documents ADD COLUMN file_path VARCHAR(255)",
            "file_size": "ALTER TABLE documents ADD COLUMN file_size INTEGER NOT NULL DEFAULT 0",
            "page_count": "ALTER TABLE documents ADD COLUMN page_count INTEGER",
            "chunk_count": "ALTER TABLE documents ADD COLUMN chunk_count INTEGER NOT NULL DEFAULT 0",
            "embed_model": "ALTER TABLE documents ADD COLUMN embed_model VARCHAR(100)",
            "updated_at": "ALTER TABLE documents ADD COLUMN updated_at DATETIME",
        },
        "document_chunks": {
            "page_number": "ALTER TABLE document_chunks ADD COLUMN page_number INTEGER",
            "embedding": "ALTER TABLE document_chunks ADD COLUMN embedding BLOB",
        },
        "messages": {
            "image_path": "ALTER TABLE messages ADD COLUMN image_path VARCHAR(255)",
            "image_mime": "ALTER TABLE messages ADD COLUMN image_mime VARCHAR(50)",
        },
    }
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, stmts in wanted.items():
            cols = {c["name"] for c in insp.get_columns(table)}
            for name, sql in stmts.items():
                if name not in cols:
                    conn.execute(text(sql))
