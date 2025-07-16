"""Initialize and manage scan target directories."""

from pathlib import Path
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.handler import get_connection


def initialize_scan_targets():
    """Create scan_targets table if it doesn't exist."""
    sql = """
    CREATE TABLE IF NOT EXISTS scan_targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT NOT NULL UNIQUE,
        active BOOLEAN NOT NULL DEFAULT 1,
        note TEXT DEFAULT NULL,
        last_scanned_at TEXT
    )
    """
    with get_connection() as conn:
        conn.execute(sql)
        conn.commit()


def add_scan_target(path: str, note: str | None = None):
    """Add a directory path into scan_targets as active."""
    full_path = str(Path(path).resolve())
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO scan_targets (path, active, note) VALUES (?, 1, ?)",
            (full_path, note),
        )
        conn.commit()


def list_scan_targets():
    """Print all registered scan target directories."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, path, active, note FROM scan_targets ORDER BY id"
        ).fetchall()

    print("\N{file folder} 登録ディレクトリ一覧")
    for row in rows:
        status = "✔ 有効" if row["active"] else "✘ 無効"
        note = f" （{row['note']}）" if row["note"] else ""
        print(f"- ID:{row['id']} | {status} | {row['path']}{note}")


if __name__ == "__main__":
    initialize_scan_targets()
    add_scan_target("D:/DL/2025_07", "2025年7月DL分")
    add_scan_target("D:/DL/2025_06", "保留中")
    list_scan_targets()
