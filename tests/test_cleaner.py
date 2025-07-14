import os
import sys
import sqlite3
from pathlib import Path
from contextlib import contextmanager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sync.cleaner as cleaner


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

    monkeypatch.setattr(cleaner, "get_connection", _connect)


def test_delete_works_with_missing_folders(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    conn = setup_db(db_path)
    existing = tmp_path / "exist"
    existing.mkdir()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status)"
        " VALUES (1, ?, 'n1', 1, 'pending')",
        (str(existing),),
    )
    cur.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status)"
        " VALUES (2, ?, 'n2', 1, 'pending')",
        (str(tmp_path / "missing"),),
    )
    conn.commit()
    conn.close()

    patch_get_connection(monkeypatch, db_path)
    cleaner.delete_works_with_missing_folders()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    ids = [row["id"] for row in conn.execute("SELECT id FROM works ORDER BY id").fetchall()]
    conn.close()
    assert ids == [1]


def test_get_all_db_folder_paths(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    conn = setup_db(db_path)
    p1 = tmp_path / "p1"
    p2 = tmp_path / "p2"
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status)"
        " VALUES (1, ?, 'n1', 1, 'pending')",
        (str(p1),),
    )
    cur.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status)"
        " VALUES (2, ?, 'n2', 1, 'pending')",
        (str(p2),),
    )
    conn.commit()
    conn.close()

    patch_get_connection(monkeypatch, db_path)
    result = cleaner.get_all_db_folder_paths()
    expected = {str(p1.resolve()), str(p2.resolve())}
    assert result == expected


def test_delete_physical_folders_not_in_db(tmp_path, monkeypatch):
    base = tmp_path / "base"
    base.mkdir()
    keep = base / "keep"
    keep.mkdir()
    remove = base / "remove"
    remove.mkdir()

    monkeypatch.setattr(cleaner, "BASE_DIRS", [str(base)])
    monkeypatch.setattr(cleaner, "get_all_db_folder_paths", lambda: {str(keep.resolve())})

    cleaner.delete_physical_folders_not_in_db(dry_run=False)

    assert keep.exists()
    assert not remove.exists()


def test_delete_folders_with_zero_images(tmp_path, monkeypatch):
    base = tmp_path / "base"
    base.mkdir()
    empty = base / "empty"
    empty.mkdir()
    filled = base / "filled"
    filled.mkdir()
    (filled / "img.jpg").write_bytes(b"x")

    monkeypatch.setattr(cleaner, "BASE_DIRS", [str(base)])

    cleaner.delete_folders_with_zero_images(dry_run=False)

    assert filled.exists()
    assert not empty.exists()


def test_delete_orphan_relations(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    conn = setup_db(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status)"
        " VALUES (1, 'p', 'o', 1, 'pending')"
    )
    cur.execute(
        "INSERT INTO work_circle_authors (work_id, circle_id, author_id) VALUES (1,1,NULL)"
    )
    cur.execute(
        "INSERT INTO work_sources (work_id, source_id) VALUES (1,1)"
    )
    cur.execute(
        "INSERT INTO work_completion_state (work_id) VALUES (1)"
    )
    # orphan entries for work_id = 2
    cur.execute(
        "INSERT INTO work_circle_authors (work_id, circle_id, author_id) VALUES (2,1,NULL)"
    )
    cur.execute(
        "INSERT INTO work_sources (work_id, source_id) VALUES (2,1)"
    )
    cur.execute(
        "INSERT INTO work_completion_state (work_id) VALUES (2)"
    )
    conn.commit()
    conn.close()

    patch_get_connection(monkeypatch, db_path)
    cleaner.delete_orphan_relations()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM work_circle_authors WHERE work_id = 2")
    assert cur.fetchone()["cnt"] == 0
    cur.execute("SELECT COUNT(*) AS cnt FROM work_sources WHERE work_id = 2")
    assert cur.fetchone()["cnt"] == 0
    cur.execute("SELECT COUNT(*) AS cnt FROM work_completion_state WHERE work_id = 2")
    assert cur.fetchone()["cnt"] == 0
    # valid rows remain
    cur.execute("SELECT COUNT(*) AS cnt FROM work_circle_authors WHERE work_id = 1")
    assert cur.fetchone()["cnt"] == 1
    conn.close()


def test_delete_physical_folders_base_missing(tmp_path, monkeypatch, capsys):
    missing = tmp_path / "missing"
    monkeypatch.setattr(cleaner, "BASE_DIRS", [str(missing)])
    monkeypatch.setattr(cleaner, "get_all_db_folder_paths", lambda: set())

    cleaner.delete_physical_folders_not_in_db(dry_run=True)

    out = capsys.readouterr().out
    assert "削除候補 0 件" in out


def test_delete_physical_folders_skips_file(tmp_path, monkeypatch):
    base = tmp_path / "base"
    base.mkdir()
    file_item = base / "note.txt"
    file_item.write_text("x", encoding="utf-8")
    to_remove = base / "remove"
    to_remove.mkdir()

    monkeypatch.setattr(cleaner, "BASE_DIRS", [str(base)])
    monkeypatch.setattr(cleaner, "get_all_db_folder_paths", lambda: set())

    cleaner.delete_physical_folders_not_in_db(dry_run=False)

    assert file_item.exists()
    assert not to_remove.exists()


def test_delete_physical_folders_dry_run(tmp_path, monkeypatch, capsys):
    base = tmp_path / "base"
    base.mkdir()
    target = base / "target"
    target.mkdir()

    monkeypatch.setattr(cleaner, "BASE_DIRS", [str(base)])
    monkeypatch.setattr(cleaner, "get_all_db_folder_paths", lambda: set())

    cleaner.delete_physical_folders_not_in_db(dry_run=True)

    out = capsys.readouterr().out
    assert "[unregistered]" in out
    assert "削除候補 1 件" in out
    assert target.exists()


def test_delete_physical_folders_rmtree_error(tmp_path, monkeypatch, capsys):
    base = tmp_path / "base"
    base.mkdir()
    bad = base / "bad"
    bad.mkdir()

    monkeypatch.setattr(cleaner, "BASE_DIRS", [str(base)])
    monkeypatch.setattr(cleaner, "get_all_db_folder_paths", lambda: set())

    def fail(_path):
        raise OSError("boom")

    monkeypatch.setattr(cleaner.shutil, "rmtree", fail)

    cleaner.delete_physical_folders_not_in_db(dry_run=False)

    out = capsys.readouterr().out
    assert "[error]" in out
    assert bad.exists()


def test_delete_folders_with_zero_images_base_missing(tmp_path, monkeypatch, capsys):
    missing = tmp_path / "missing"
    monkeypatch.setattr(cleaner, "BASE_DIRS", [str(missing)])
    cleaner.delete_folders_with_zero_images(dry_run=True)
    out = capsys.readouterr().out
    assert "画像0枚フォルダ候補 0 件" in out


def test_delete_folders_with_zero_images_skip_file(tmp_path, monkeypatch):
    base = tmp_path / "base"
    base.mkdir()
    file_item = base / "note.txt"
    file_item.write_text("x", encoding="utf-8")
    empty = base / "empty"
    empty.mkdir()

    monkeypatch.setattr(cleaner, "BASE_DIRS", [str(base)])
    monkeypatch.setattr(cleaner, "count_images", lambda _p: 0)

    cleaner.delete_folders_with_zero_images(dry_run=False)

    assert file_item.exists()
    assert not empty.exists()


def test_delete_folders_with_zero_images_dry_run(tmp_path, monkeypatch, capsys):
    base = tmp_path / "base"
    base.mkdir()
    empty = base / "empty"
    empty.mkdir()

    monkeypatch.setattr(cleaner, "BASE_DIRS", [str(base)])
    monkeypatch.setattr(cleaner, "count_images", lambda _p: 0)

    cleaner.delete_folders_with_zero_images(dry_run=True)

    out = capsys.readouterr().out
    assert "[zero]" in out
    assert "画像0枚フォルダ候補 1 件" in out
    assert empty.exists()


def test_delete_folders_with_zero_images_rmtree_error(tmp_path, monkeypatch, capsys):
    base = tmp_path / "base"
    base.mkdir()
    bad = base / "bad"
    bad.mkdir()

    monkeypatch.setattr(cleaner, "BASE_DIRS", [str(base)])
    monkeypatch.setattr(cleaner, "count_images", lambda _p: 0)

    def fail(_p):
        raise OSError("err")

    monkeypatch.setattr(cleaner.shutil, "rmtree", fail)

    cleaner.delete_folders_with_zero_images(dry_run=False)

    out = capsys.readouterr().out
    assert "[error]" in out
    assert bad.exists()
