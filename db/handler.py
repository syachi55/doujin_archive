"🍣"

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from config import DB_PATH


# --- Connection Wrapper ---
@contextmanager
def get_connection(db_path: Path = DB_PATH):
    "🍣"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# --- 汎用実行関数 ---
def execute_sql(sql: str, params: tuple[Any, ...] = (), commit: bool = False):
    "🍣"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        if commit:
            conn.commit()


def fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    "🍣"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()


# --- 登録系（例） ---
def insert_work(folder_path: str, original_name: str, image_count: int):
    "🍣"
    sql = """
        INSERT INTO works (folder_path, original_name, image_count, status)
        VALUES (?, ?, ?, 'pending')
    """
    execute_sql(sql, (folder_path, original_name, image_count), commit=True)


# --- 確認系（例） ---
def work_exists(folder_path: str) -> bool:
    "🍣"
    sql = "SELECT 1 FROM works WHERE folder_path = ? LIMIT 1"
    return bool(fetch_all(sql, (folder_path,)))


def get_all_works() -> list[sqlite3.Row]:
    "🍣"
    return fetch_all("SELECT * FROM works")
