import os
import sys
import sqlite3
import csv
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import folders.rename as rename
from utils.normalizer import normalize_for_filename


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
    monkeypatch.setattr(rename, "get_connection", _connect)


def test_compose_folder_name(tmp_path, monkeypatch):
    db_path = tmp_path / "test.sqlite"
    conn = setup_db(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO types (id,name) VALUES (1,'CG集')")
    cur.execute("INSERT INTO circles (id,name) VALUES (1,'C1'),(2,'C2')")
    cur.execute("INSERT INTO authors (id,name) VALUES (1,'A1')")
    cur.execute("INSERT INTO sources (id,name) VALUES (1,'S1'),(2,'S2')")
    cur.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status, type_id, title)"
        " VALUES (1, 'p', 'orig', 0, 'pending', 1, 'Title')"
    )
    cur.execute("INSERT INTO work_circle_authors (work_id,circle_id,author_id) VALUES (1,1,1)")
    cur.execute("INSERT INTO work_circle_authors (work_id,circle_id,author_id) VALUES (1,2,NULL)")
    cur.execute("INSERT INTO work_sources (work_id,source_id) VALUES (1,1)")
    cur.execute("INSERT INTO work_sources (work_id,source_id) VALUES (1,2)")
    conn.commit()
    conn.close()

    patch_get_connection(monkeypatch, db_path)

    result = rename.compose_folder_name(1)
    expected = normalize_for_filename('｛CG集｝[C1 (A1)、C2] Title （S1、S2）')
    assert result == expected


def test_rename_one_work(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    conn = setup_db(db_path)
    old_dir = tmp_path / "old"
    old_dir.mkdir()
    conn.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status, title)"
        " VALUES (1, ?, 'orig', 1, 'pending', 'T1')",
        (str(old_dir),),
    )
    conn.commit()
    conn.close()

    patch_get_connection(monkeypatch, db_path)
    monkeypatch.setattr(rename, "compose_folder_name", lambda _id: "new")

    assert rename.rename_one_work(1)
    new_path = tmp_path / "new"
    assert new_path.exists()
    assert not old_dir.exists()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT folder_path, status FROM works WHERE id = 1").fetchone()
    conn.close()
    assert row["folder_path"] == str(new_path)
    assert row["status"] == "renamed"


def test_rename_all_confirmed_works(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    conn = setup_db(db_path)
    old_dir = tmp_path / "old"
    old_dir.mkdir()
    conn.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status, title)"
        " VALUES (1, ?, 'orig', 1, 'confirmed', 'T')",
        (str(old_dir),),
    )
    conn.execute(
        "INSERT INTO work_completion_state (work_id,circle_id_done,author_id_done,source_id_done,type_id_done,title_done)"
        " VALUES (1,1,1,1,1,1)"
    )
    conn.commit()
    conn.close()

    patch_get_connection(monkeypatch, db_path)
    monkeypatch.setattr(rename, "compose_folder_name", lambda _id: "new")
    class DummyDatetime:
        @classmethod
        def now(cls):
            return datetime(2022, 1, 2)
    monkeypatch.setattr(rename, "datetime", DummyDatetime)
    monkeypatch.chdir(tmp_path)

    rename.rename_all_confirmed_works()

    new_path = tmp_path / "new"
    assert new_path.exists()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT folder_path, status FROM works WHERE id = 1").fetchone()
    conn.close()
    assert row["folder_path"] == str(new_path)
    assert row["status"] == "renamed"

    log_path = tmp_path / "data" / "logs" / "rename_20220102.csv"
    assert log_path.is_file()
# Additional tests for edge cases

import pytest


def test_compose_folder_name_missing(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    setup_db(db_path).close()
    patch_get_connection(monkeypatch, db_path)
    with pytest.raises(ValueError):
        rename.compose_folder_name(99)


def test_rename_one_work_missing_id(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "db.sqlite"
    setup_db(db_path).close()
    patch_get_connection(monkeypatch, db_path)
    assert not rename.rename_one_work(1)
    captured = capsys.readouterr()
    assert "work_id=1" in captured.out


def test_rename_one_work_missing_old_path(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "db.sqlite"
    conn = setup_db(db_path)
    path = tmp_path / "missing"
    conn.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status, title)"
        " VALUES (1, ?, 'o', 0, 'pending', 'T')",
        (str(path),),
    )
    conn.commit()
    conn.close()
    patch_get_connection(monkeypatch, db_path)
    monkeypatch.setattr(rename, "compose_folder_name", lambda _id: "new")
    assert not rename.rename_one_work(1)
    captured = capsys.readouterr()
    assert "存在しません" in captured.out


def test_rename_one_work_new_path_exists(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "db.sqlite"
    conn = setup_db(db_path)
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()
    conn.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status, title)"
        " VALUES (1, ?, 'o', 0, 'pending', 'T')",
        (str(old_dir),),
    )
    conn.commit()
    conn.close()
    patch_get_connection(monkeypatch, db_path)
    monkeypatch.setattr(rename, "compose_folder_name", lambda _id: "new")
    assert not rename.rename_one_work(1)
    captured = capsys.readouterr()
    assert "既に存在" in captured.out
    assert old_dir.exists()


def prepare_confirmed(db_path: Path, folder: Path) -> None:
    conn = setup_db(db_path)
    conn.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status, title)"
        " VALUES (1, ?, 'o', 0, 'confirmed', 'T')",
        (str(folder),),
    )
    conn.execute(
        "INSERT INTO work_completion_state (work_id,circle_id_done,author_id_done,source_id_done,type_id_done,title_done)"
        " VALUES (1,1,1,1,1,1)"
    )
    conn.commit()
    conn.close()


def run_confirmed(monkeypatch, db_path: Path, date: datetime, tmp_path: Path):
    patch_get_connection(monkeypatch, db_path)
    monkeypatch.setattr(rename, "compose_folder_name", lambda _id: "new")
    class DummyDatetime:
        @classmethod
        def now(cls):
            return date
    monkeypatch.setattr(rename, "datetime", DummyDatetime)
    monkeypatch.chdir(tmp_path)
    rename.rename_all_confirmed_works()


def read_log(tmp_path: Path, date: datetime) -> list:
    log_path = tmp_path / "data" / "logs" / f"rename_{date:%Y%m%d}.csv"
    with open(log_path, encoding="utf-8-sig") as f:
        return list(csv.reader(f))[1:]


def test_rename_all_confirmed_missing_old(tmp_path, monkeypatch):
    db = tmp_path / "db.sqlite"
    folder = tmp_path / "old"
    folder.mkdir()
    prepare_confirmed(db, folder)
    # remove folder before running
    os.rmdir(folder)
    run_confirmed(monkeypatch, db, datetime(2022, 1, 3), tmp_path)
    logs = read_log(tmp_path, datetime(2022, 1, 3))
    assert logs[0][3] == "error"
    assert "missing" in logs[0][4]


def test_rename_all_confirmed_new_exists(tmp_path, monkeypatch):
    db = tmp_path / "db.sqlite"
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()
    prepare_confirmed(db, old_dir)
    run_confirmed(monkeypatch, db, datetime(2022, 1, 4), tmp_path)
    logs = read_log(tmp_path, datetime(2022, 1, 4))
    assert logs[0][3] == "skipped"


def test_rename_all_confirmed_exception(tmp_path, monkeypatch):
    db = tmp_path / "db.sqlite"
    folder = tmp_path / "old"
    folder.mkdir()
    prepare_confirmed(db, folder)
    patch_get_connection(monkeypatch, db)
    monkeypatch.setattr(rename, "compose_folder_name", lambda _id: "new")
    def fail(*args, **kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr(os, "rename", fail)
    class DummyDatetime:
        @classmethod
        def now(cls):
            return datetime(2022, 1, 5)
    monkeypatch.setattr(rename, "datetime", DummyDatetime)
    monkeypatch.chdir(tmp_path)
    rename.rename_all_confirmed_works()
    logs = read_log(tmp_path, datetime(2022, 1, 5))
    assert logs[0][3] == "error"
    assert "boom" in logs[0][4]
