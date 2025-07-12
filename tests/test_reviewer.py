import os
import sys
import sqlite3
from pathlib import Path
from contextlib import contextmanager
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import analyze.analyzer as analyzer
import analyze.reviewer as reviewer
from analyze.analyzer import parse_original_names
from analyze.reviewer import get_or_create_id, apply_draft_to_works
import db.handler as handler


def setup_db(path: Path):
    with open(Path(__file__).resolve().parents[1] / "db" / "schema.sql", "r") as f:
        schema = f.read()
    conn = sqlite3.connect(path)
    conn.executescript(schema)
    conn.execute("ALTER TABLE works ADD COLUMN circle_id INTEGER")
    conn.execute("ALTER TABLE works ADD COLUMN author_id INTEGER")
    conn.execute("ALTER TABLE works ADD COLUMN source_id INTEGER")
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
    monkeypatch.setattr(analyzer, "get_connection", _connect)
    monkeypatch.setattr(reviewer, "get_connection", _connect)


def test_get_or_create_id_existing():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("CREATE TABLE circles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)")
    cur.execute("INSERT INTO circles (name) VALUES ('FooBar')")
    existing_id = cur.lastrowid
    conn.commit()

    result = get_or_create_id(cur, "circles", "foo bar")
    assert result == existing_id
    cur.execute("SELECT COUNT(*) AS cnt FROM circles")
    assert cur.fetchone()["cnt"] == 1
    conn.close()


def test_get_or_create_id_new():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("CREATE TABLE circles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)")
    conn.commit()

    result = get_or_create_id(cur, "circles", "B/L?o*g")
    cur.execute("SELECT name FROM circles WHERE id = ?", (result,))
    name = cur.fetchone()["name"]
    assert name == "B／L？o＊g"
    conn.close()


def test_parse_original_names(tmp_path, monkeypatch):
    db_path = tmp_path / "test.sqlite"
    monkeypatch.setattr(handler, "DB_PATH", db_path)
    patch_get_connection(monkeypatch, db_path)
    conn = setup_db(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO works (id, folder_path, original_name, image_count, status) VALUES (1, 'p1', '｛CG集｝[C1] T1 (S1)', 10, 'pending')")
    cur.execute("INSERT INTO works (id, folder_path, original_name, image_count, status) VALUES (2, 'p2', 'random text', 5, 'pending')")
    conn.commit()
    conn.close()

    parse_original_names()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM works_draft ORDER BY work_id")
    rows = cur.fetchall()
    assert len(rows) == 2
    row1 = rows[0]
    assert row1["circle_raw"] == "C1"
    assert row1["title_raw"] == "T1"
    assert row1["source_raw"] == "S1"
    row2 = rows[1]
    assert row2["title_raw"] == "random text"
    conn.close()


def test_apply_draft_to_works(tmp_path, monkeypatch):
    db_path = tmp_path / "test.sqlite"
    monkeypatch.setattr(handler, "DB_PATH", db_path)
    patch_get_connection(monkeypatch, db_path)
    conn = setup_db(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO works (id, folder_path, original_name, image_count, status) VALUES (1, 'p1', 'name', 10, 'pending')")
    cur.execute("INSERT INTO works_draft (work_id, circle_raw, author_raw, source_raw, type_raw, title_raw) VALUES (1, 'Circle', 'Author', 'Magazine', 'TypeA', 'Title1')")
    conn.commit()
    conn.close()

    apply_draft_to_works()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    work = cur.execute("SELECT * FROM works WHERE id = 1").fetchone()
    assert work["title"] == "Title1"
    assert work["circle_id"] == 1
    assert work["author_id"] == 1
    assert work["source_id"] == 1
    assert work["type_id"] == 1
    state = cur.execute("SELECT * FROM work_completion_state WHERE work_id = 1").fetchone()
    assert state["circle_id_done"] == 1
    assert state["author_id_done"] == 1
    assert state["source_id_done"] == 1
    assert state["type_id_done"] == 1
    conn.close()
