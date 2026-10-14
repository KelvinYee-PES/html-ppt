"""SQLite store for brand profiles and associated assets."""
from __future__ import annotations

import datetime
import json
import sqlite3
from pathlib import Path
from typing import Optional

from htmlppt.brand.model import BrandProfile


class BrandStore:
    def __init__(self, db_path: str | Path = "data/brands.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS brands (
                    id TEXT PRIMARY KEY,
                    organization TEXT NOT NULL,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    data BLOB NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_brand(self, brand: BrandProfile) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        data = brand.model_dump_json()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO brands (id, organization, name, data, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (brand.id, brand.organization, brand.name, data, now),
            )
            conn.commit()

    def get_brand(self, brand_id: str) -> BrandProfile | None:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT data FROM brands WHERE id = ?", (brand_id,))
            row = cur.fetchone()
            if not row:
                return None
            return BrandProfile.model_validate_json(row["data"])

    def list_brands(self, organization: str | None = None) -> list[BrandProfile]:
        with self._get_conn() as conn:
            if organization:
                cur = conn.execute("SELECT data FROM brands WHERE organization = ? ORDER BY updated_at DESC", (organization,))
            else:
                cur = conn.execute("SELECT data FROM brands ORDER BY updated_at DESC")
            return [BrandProfile.model_validate_json(row["data"]) for row in cur.fetchall()]

    def delete_brand(self, brand_id: str) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute("DELETE FROM brands WHERE id = ?", (brand_id,))
            conn.commit()
            return cur.rowcount > 0

    def save_file(self, file_id: str, filename: str, content_type: str, data: bytes) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO files (id, filename, content_type, data, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (file_id, filename, content_type, data, now),
            )
            conn.commit()

    def get_file(self, file_id: str) -> tuple[str, str, bytes] | None:
        """Returns (filename, content_type, bytes)."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT filename, content_type, data FROM files WHERE id = ?", (file_id,))
            row = cur.fetchone()
            if not row:
                return None
            return row["filename"], row["content_type"], row["data"]
