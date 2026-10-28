"""Small SQLite-backed persistence for dashboard cases and audit records."""

import json
import os
import sqlite3
from contextlib import contextmanager
from typing import List, Tuple


class SQLiteCaseAuditStore:
    """Persist complete case and audit snapshots in a local SQLite file."""

    def __init__(self, database_path: str):
        self.database_path = os.fspath(database_path)
        parent = os.path.dirname(os.path.abspath(self.database_path))
        os.makedirs(parent, exist_ok=True)
        with self._connection() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS cases (position INTEGER PRIMARY KEY, case_id TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS audit_entries (position INTEGER PRIMARY KEY, entry_id TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS app_settings (setting_key TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )

    def load_state(self) -> Tuple[List[dict], List[dict]]:
        with self._connection() as connection:
            case_rows = connection.execute(
                "SELECT payload FROM cases ORDER BY position"
            ).fetchall()
            audit_rows = connection.execute(
                "SELECT payload FROM audit_entries ORDER BY position"
            ).fetchall()
        cases = [json.loads(row[0]) for row in case_rows]
        audit_entries = [json.loads(row[0]) for row in audit_rows]
        return cases, audit_entries

    def save_state(self, cases: List[dict], audit_entries: List[dict]) -> None:
        """Replace both snapshots together so a save cannot persist only half a review."""
        with self._connection() as connection:
            connection.execute("DELETE FROM cases")
            connection.execute("DELETE FROM audit_entries")
            connection.executemany(
                "INSERT INTO cases (position, case_id, payload) VALUES (?, ?, ?)",
                [
                    (index, case["id"], json.dumps(case, ensure_ascii=False))
                    for index, case in enumerate(cases)
                ],
            )
            connection.executemany(
                "INSERT INTO audit_entries (position, entry_id, payload) VALUES (?, ?, ?)",
                [
                    (index, entry["id"], json.dumps(entry, ensure_ascii=False))
                    for index, entry in enumerate(audit_entries)
                ],
            )

    def load_settings(self) -> dict | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT payload FROM app_settings WHERE setting_key = ?",
                ("system",),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def save_settings(self, settings: dict) -> None:
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO app_settings (setting_key, payload) VALUES (?, ?) "
                "ON CONFLICT(setting_key) DO UPDATE SET payload = excluded.payload",
                ("system", json.dumps(settings, ensure_ascii=False)),
            )

    @contextmanager
    def _connection(self):
        """Commit a database operation and always release its file handle."""
        connection = sqlite3.connect(self.database_path)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
