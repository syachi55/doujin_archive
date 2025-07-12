"🍣"

# io/rename.py

import os
import csv
from datetime import datetime
from utils.normalizer import normalize_for_filename
from db.handler import get_connection


def compose_folder_name(work_id: int) -> str:
    "work_id に対応する新しいフォルダ名を構築する"

    with get_connection() as conn:
        cur = conn.cursor()

        # works.title, type名
        cur.execute(
            """
            SELECT w.title, t.name AS type_name
            FROM works w
            LEFT JOIN types t ON w.type_id = t.id
            WHERE w.id = ?
        """,
            (work_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"work_id {work_id} が存在しません")

        title = row["title"]
        type_name = row["type_name"]

        # work_circle_authors: {circle_id, author_id} → name
        cur.execute(
            """
            SELECT c.name AS circle_name, a.name AS author_name
            FROM work_circle_authors wca
            JOIN circles c ON wca.circle_id = c.id
            LEFT JOIN authors a ON wca.author_id = a.id
            WHERE wca.work_id = ?
        """,
            (work_id,),
        )
        circle_map = {}
        for row in cur.fetchall():
            c = row["circle_name"]
            a = row["author_name"]
            circle_map.setdefault(c, []).append(a)

        # work_sources: source名
        cur.execute(
            """
            SELECT s.name AS source_name
            FROM work_sources ws
            JOIN sources s ON ws.source_id = s.id
            WHERE ws.work_id = ?
        """,
            (work_id,),
        )
        sources = [row["source_name"] for row in cur.fetchall()]

    # --- フォルダ名構築 ---
    # 1. [サークル (作者1、作者2)、サークル] の部分
    circle_parts = []
    for circle, authors in circle_map.items():
        if authors and any(a for a in authors):
            authors_str = "、".join(a for a in authors if a)
            part = f"{circle} ({authors_str})"
        else:
            part = circle
        circle_parts.append(part)
    circle_section = "、".join(circle_parts)

    # 2. (ソース1、ソース2)
    source_section = f"（{'、'.join(sources)}）" if sources else ""

    # 3. 全体構成
    parts = [f"｛{type_name}｝[{circle_section}]", title]
    if source_section:
        parts.append(source_section)
    parts.append(f"#id{work_id}")
    raw_name = " ".join(parts)
    return normalize_for_filename(raw_name)


def rename_one_work(work_id: int) -> bool:
    """
    指定 work_id のフォルダをリネームし、DBも更新する
    成功すれば True、既に存在・失敗した場合は False
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # 現在のパスを取得
        cur.execute("SELECT folder_path FROM works WHERE id = ?", (work_id,))
        row = cur.fetchone()
        if not row:
            print(f"[skip] work_id={work_id} が存在しません")
            return False

        old_path = row["folder_path"]
        if not os.path.exists(old_path):
            print(f"[error] フォルダが存在しません: {old_path}")
            return False

        # 新しいフォルダ名を構築
        new_folder_name = compose_folder_name(work_id)
        base_dir = os.path.dirname(old_path)
        new_path = os.path.join(base_dir, new_folder_name)

        # すでに存在するならスキップ（上書き防止）
        if os.path.exists(new_path):
            print(f"[skip] 既に存在: {new_path}")
            return False

        # 実際のリネーム
        os.rename(old_path, new_path)
        print(f"[renamed] {old_path} → {new_path}")

        # DB更新（パスと status）
        cur.execute(
            """
            UPDATE works
            SET folder_path = ?, status = 'renamed'
            WHERE id = ?
        """,
            (new_path, work_id),
        )
        conn.commit()

        return True


def rename_all_confirmed_works():
    """
    補完完了かつ confirmed な works を一括リネーム＋CSVログ出力
    """
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT w.id, w.folder_path
            FROM works w
            JOIN work_completion_state s ON w.id = s.work_id
            WHERE w.status = 'confirmed'
              AND s.circle_id_done = 1
              AND s.author_id_done = 1
              AND s.source_id_done = 1
              AND s.type_id_done = 1
              AND s.title_done = 1
        """
        )
        records = cur.fetchall()

    print(f"🔍 リネーム対象: {len(records)} 件")

    log_rows = []
    renamed = skipped = failed = 0

    for row in records:
        work_id = row["id"]
        old_path = row["folder_path"]
        try:
            new_name = compose_folder_name(work_id)
            base_dir = os.path.dirname(old_path)
            new_path = os.path.join(base_dir, new_name)

            if not os.path.exists(old_path):
                log_rows.append([work_id, old_path, "", "error", "missing folder"])
                print(f"[error] フォルダが存在しません: {old_path}")
                failed += 1
                continue

            if os.path.exists(new_path):
                log_rows.append(
                    [work_id, old_path, new_path, "skipped", "already exists"]
                )
                print(f"[skip] 既に存在: {new_path}")
                skipped += 1
                continue

            # 実行・成功記録
            os.rename(old_path, new_path)
            with get_connection() as conn:
                conn.execute(
                    """
                    UPDATE works SET folder_path = ?, status = 'renamed' WHERE id = ?
                """,
                    (new_path, work_id),
                )
                conn.commit()

            log_rows.append([work_id, old_path, new_path, "renamed", ""])
            print(f"[renamed] {old_path} → {new_path}")
            renamed += 1

        except Exception as e:  # pylint: disable=broad-exception-caught
            log_rows.append([work_id, old_path, "", "error", str(e)])
            print(f"[error] work_id={work_id}: {e}")
            failed += 1

    # ログ書き出し
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    filename = f"rename_{datetime.now():%Y%m%d}.csv"
    log_path = os.path.join(log_dir, filename)
    with open(log_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["work_id", "old_path", "new_path", "status", "reason"])
        writer.writerows(log_rows)

    print(f"📄 ログ出力完了: {log_path}")
    print(f"✅ renamed: {renamed} / ⏩ skipped: {skipped} / ❌ error: {failed}")
