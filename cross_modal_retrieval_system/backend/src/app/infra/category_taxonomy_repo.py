import sqlite3
import threading
from pathlib import Path

from app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class CategoryTaxonomyRepository:
    """
    Maintain category taxonomy with two tables:
    1) super_categories(id, name)
    2) sub_categories(id, name, super_category_id)
    """

    def __init__(self, db_path: str):
        path = Path(db_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._lock = threading.Lock()
        self._init_tables()

    def _init_tables(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS super_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sub_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    super_category_id INTEGER NOT NULL,
                    UNIQUE(name, super_category_id),
                    FOREIGN KEY(super_category_id) REFERENCES super_categories(id)
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sub_categories_super_id
                ON sub_categories(super_category_id)
                """
            )
            self._conn.commit()

    def get_or_create_super_category(self, name: str) -> int:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("super category name cannot be empty")

        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT id FROM super_categories WHERE name = ?", (cleaned,))
            row = cur.fetchone()
            if row:
                return int(row[0])

            cur.execute("INSERT INTO super_categories(name) VALUES (?)", (cleaned,))
            self._conn.commit()
            return int(cur.lastrowid)

    def get_or_create_sub_category(self, name: str, super_category_id: int) -> int:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("sub category name cannot be empty")

        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT id FROM sub_categories WHERE name = ? AND super_category_id = ?",
                (cleaned, super_category_id),
            )
            row = cur.fetchone()
            if row:
                return int(row[0])

            cur.execute(
                "INSERT INTO sub_categories(name, super_category_id) VALUES (?, ?)",
                (cleaned, super_category_id),
            )
            self._conn.commit()
            return int(cur.lastrowid)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

taxonomy_repo = CategoryTaxonomyRepository(settings.category_taxonomy_db_path)