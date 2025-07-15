import os
import sys
import sqlite3
from pathlib import Path
from contextlib import contextmanager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sync.reconciler as reconciler


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

    monkeypatch.setattr(reconciler, "get_connection", _connect)


def test_get_all_db_paths(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    conn = setup_db(db_path)
    cur = conn.cursor()
    p1 = tmp_path / "p1"
    p2 = tmp_path / "p2"
    cur.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status)"
        " VALUES (1, ?, 'orig1', 1, 'pending')",
        (str(p1),),
    )
    cur.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status)"
        " VALUES (2, ?, 'orig2', 2, 'pending')",
        (str(p2),),
    )
    conn.commit()
    conn.close()

    patch_get_connection(monkeypatch, db_path)

    result = reconciler.get_all_db_paths()
    expected = {
        str(p1.resolve()): (1, "orig1"),
        str(p2.resolve()): (2, "orig2"),
    }
    assert result == expected


def test_get_all_physical_folders(tmp_path, monkeypatch):
    base = tmp_path / "base"
    base.mkdir()
    f1 = base / "A"
    f1.mkdir()
    f2 = base / "B"
    f2.mkdir()
    (base / "notdir.txt").write_text("x", encoding="utf-8")

    monkeypatch.setattr(reconciler, "BASE_DIRS", [str(base)])

    result = reconciler.get_all_physical_folders()
    assert set(result) == {f1.resolve(), f2.resolve()}


def test_get_all_physical_folders_missing_base(tmp_path, monkeypatch, capsys):
    missing = tmp_path / "missing"
    base = tmp_path / "base"
    base.mkdir()
    d1 = base / "A"
    d1.mkdir()
    d2 = base / "B"
    d2.mkdir()
    (base / "note.txt").write_text("x", encoding="utf-8")

    monkeypatch.setattr(reconciler, "BASE_DIRS", [str(missing), str(base)])

    result = reconciler.get_all_physical_folders()
    out = capsys.readouterr().out
    assert f"[warn] base directory not found: {missing}" in out
    assert set(result) == {d1.resolve(), d2.resolve()}


def test_compare_db_and_folders(capsys, tmp_path, monkeypatch):
    p1 = (tmp_path / "p1").resolve()
    p2 = (tmp_path / "p2").resolve()
    p3 = (tmp_path / "p3").resolve()

    monkeypatch.setattr(
        reconciler,
        "get_all_db_paths",
        lambda: {str(p1): (1, "O1"), str(p2): (2, "O2")},
    )
    monkeypatch.setattr(
        reconciler,
        "get_all_physical_folders",
        lambda: [p2, p3],
    )

    reconciler.compare_db_and_folders()
    out = capsys.readouterr().out
    assert "DB登録：2 件" in out
    assert "実フォルダ：2 件" in out
    assert "❌ 実体が存在しない（DBにだけある）：1 件" in out
    assert "➕ 未登録（物理にだけある）：1 件" in out
