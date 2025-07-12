import os
import sys
import sqlite3
from pathlib import Path
from contextlib import contextmanager
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import db.handler as handler
import db.loader as loader


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
    monkeypatch.setattr(handler, "get_connection", _connect)


# --- handler.get_connection ---
def test_get_connection_closes(tmp_path):
    db_path = tmp_path / "db.sqlite"
    with handler.get_connection(db_path) as conn:
        assert conn.row_factory == sqlite3.Row
        conn.execute("CREATE TABLE sample(id INTEGER)")
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


# --- insert_work, work_exists, get_all_works ---
def test_basic_work_functions(tmp_path, monkeypatch):
    db_path = tmp_path / "works.sqlite"
    setup_db(db_path).close()
    patch_get_connection(monkeypatch, db_path)

    assert handler.get_all_works() == []

    handler.insert_work("p1", "Name", 3)
    assert handler.work_exists("p1")
    assert not handler.work_exists("p2")

    rows = handler.get_all_works()
    assert len(rows) == 1
    row = rows[0]
    assert row["folder_path"] == "p1"
    assert row["original_name"] == "Name"
    assert row["image_count"] == 3


# --- loader helpers ---
def test_find_latest_json(tmp_path):
    base = tmp_path
    old = base / f"{loader.CLASSIFY_OUTPUT_PREFIX}_old.json"
    new = base / f"{loader.CLASSIFY_OUTPUT_PREFIX}_new.json"
    old.write_text("[]", encoding="utf-8")
    new.write_text("[]", encoding="utf-8")
    os.utime(old, (1, 1))
    os.utime(new, None)

    result = loader.find_latest_json(base)
    assert result == new

    (base / "nomatch.json").write_text("{}", encoding="utf-8")
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert loader.find_latest_json(empty_dir) is None


def test_load_classified_works(tmp_path, monkeypatch):
    db_path = tmp_path / "loader.sqlite"
    setup_db(db_path).close()
    patch_get_connection(monkeypatch, db_path)
    monkeypatch.setattr(loader, "BASE_DIRS", [str(tmp_path)])

    records = [
        {"folder_path": "p1", "original_name": "N1", "image_count": 5},
        {"folder_path": "p2", "original_name": "N2", "image_count": 7},
    ]
    json_path = tmp_path / f"{loader.CLASSIFY_OUTPUT_PREFIX}_test.json"
    json_path.write_text(json.dumps(records), encoding="utf-8")

    # Pre-insert p1 to test skipping
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO works (folder_path, original_name, image_count, status) VALUES ('p1', 'exist', 1, 'pending')")
    conn.commit()
    conn.close()

    loader.load_classified_works()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT folder_path, original_name, image_count FROM works ORDER BY folder_path").fetchall()
    conn.close()

    assert len(rows) == 2
    assert rows[0]["folder_path"] == "p1"  # existing preserved
    assert rows[0]["original_name"] == "exist"
    assert rows[1]["folder_path"] == "p2"
    assert rows[1]["original_name"] == "N2"
    assert rows[1]["image_count"] == 7
