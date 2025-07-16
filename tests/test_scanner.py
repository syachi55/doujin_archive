import os
import sys
import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import folders.scanner as scanner


def setup_db(path: Path):
    with open(Path(__file__).resolve().parents[1] / "db" / "schema.sql", "r") as f:
        schema = f.read()
    conn = sqlite3.connect(path)
    conn.executescript(schema)
    conn.row_factory = sqlite3.Row
    return conn


def patch_get_connection(monkeypatch, path: Path):
    @contextmanager
    def _connect():
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    monkeypatch.setattr(scanner, "get_connection", _connect)


class FixedDatetime:
    @classmethod
    def now(cls):
        return datetime(2022, 1, 2, 3, 4)


def test_scan_and_export(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    conn = setup_db(db_path)
    base = tmp_path / "base"
    base.mkdir()
    conn.execute(
        "INSERT INTO scan_targets (path, active) VALUES (?, 1)",
        (str(base),),
    )
    conn.commit()
    conn.close()

    (base / "A").mkdir()
    (base / "A" / "img.jpg").write_bytes(b"x")
    (base / "B").mkdir()
    (base / "B" / "img.png").write_bytes(b"x")

    patch_get_connection(monkeypatch, db_path)
    monkeypatch.setattr(scanner, "datetime", FixedDatetime)

    scanner.scan_and_export()

    json_path = base / "scan_20220102_0304.json"
    assert json_path.is_file()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    names = sorted(rec["original_name"] for rec in data)
    assert names == ["A", "B"]
    assert all(rec["status"] == "pending" for rec in data)


def test_inactive_target_ignored(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    conn = setup_db(db_path)
    active = tmp_path / "active"
    active.mkdir()
    inactive = tmp_path / "inactive"
    inactive.mkdir()
    conn.execute(
        "INSERT INTO scan_targets (path, active) VALUES (?, 1)",
        (str(active),),
    )
    conn.execute(
        "INSERT INTO scan_targets (path, active) VALUES (?, 0)",
        (str(inactive),),
    )
    conn.commit()
    conn.close()

    (active / "A").mkdir()
    (active / "A" / "img.jpg").write_bytes(b"x")
    (inactive / "B").mkdir()
    (inactive / "B" / "img.jpg").write_bytes(b"x")

    patch_get_connection(monkeypatch, db_path)
    monkeypatch.setattr(scanner, "datetime", FixedDatetime)

    scanner.scan_and_export()

    json_active = active / "scan_20220102_0304.json"
    json_inactive = inactive / "scan_20220102_0304.json"
    assert json_active.is_file()
    assert not json_inactive.exists()

    data = json.loads(json_active.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["original_name"] == "A"


def test_non_dir_entries_skipped(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    conn = setup_db(db_path)
    base = tmp_path / "base"
    base.mkdir()
    conn.execute(
        "INSERT INTO scan_targets (path, active) VALUES (?, 1)",
        (str(base),),
    )
    conn.commit()
    conn.close()

    (base / "A.txt").write_text("x", encoding="utf-8")

    patch_get_connection(monkeypatch, db_path)
    monkeypatch.setattr(scanner, "datetime", FixedDatetime)

    scanner.scan_and_export()

    json_path = base / "scan_20220102_0304.json"
    assert json_path.is_file()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data == []
