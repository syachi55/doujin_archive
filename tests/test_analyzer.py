import os
import sys
import sqlite3
from pathlib import Path
from contextlib import contextmanager
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import analyze.analyzer as analyzer
from analyze.analyzer import strip_prefix, try_match, parse_original_names


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

    monkeypatch.setattr(analyzer, "get_connection", _connect)


def test_strip_prefix():
    assert strip_prefix("〔非表示〕[Circle] Title") == "[Circle] Title"
    assert strip_prefix("NoPrefix") == "NoPrefix"


def test_try_match_with_author():
    name = "｛CG集｝[サークル (作者)] タイトル (ソース)"
    result = try_match(name)
    assert result == {
        "type": "CG集",
        "circle": "サークル",
        "author": "作者",
        "title": "タイトル",
        "source": "ソース",
    }


def test_try_match_no_author():
    name = "｛漫画｝[サークル] タイトル (ジャンプ)"
    result = try_match(name)
    assert result == {
        "type": "漫画",
        "circle": "サークル",
        "title": "タイトル",
        "source": "ジャンプ",
    }


def test_try_match_circle_title():
    name = "[サークル] タイトル1"
    result = try_match(name)
    assert result == {
        "circle": "サークル",
        "title": "タイトル",
    }


def test_try_match_none():
    assert try_match("random text") == {"title": "random text"}


def test_try_match_no_match(monkeypatch):
    monkeypatch.setattr(analyzer, "PATTERN_SEQUENCE", [])
    assert try_match("これはマッチしない文字列") is None


def test_parse_original_names_skips_unmatched(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "test.sqlite"
    conn = setup_db(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO works (id, folder_path, original_name, image_count, status)"
        " VALUES (1, 'p1', '#id123', 0, 'pending')"
    )
    conn.commit()
    conn.close()

    patch_get_connection(monkeypatch, db_path)
    parse_original_names()

    captured = capsys.readouterr().out
    assert "解析対象: 1" in captured
    assert "0 件の draft" in captured

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM works_draft").fetchall()
    conn.close()
    assert rows == []
