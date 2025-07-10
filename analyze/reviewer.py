"🍣"

# analyze/reviewer.py

from db.handler import get_connection
from utils.normalizer import normalize_for_matching, normalize_for_filename


def get_or_create_id(cursor, table: str, name: str) -> int:
    """
    指定の辞書テーブルに name を登録 or 照合付き取得

    - normalize_for_matching で表記ゆれ吸収し、既存と照合
    - 見つからなければ normalize_for_filename で保存可能形式にして新規登録
    """
    match_key = normalize_for_matching(name)

    # 表記ゆれを吸収した一致確認
    cursor.execute(f"SELECT id, name FROM {table}")
    for row in cursor.fetchall():
        existing = row["name"]
        if normalize_for_matching(existing) == match_key:
            return row["id"]

    # 一致がなければ、新たに登録（記号変換済みの安全名で）
    safe_name = normalize_for_filename(name)
    cursor.execute(f"INSERT INTO {table} (name) VALUES (?)", (safe_name,))
    return cursor.lastrowid


def apply_draft_to_works():
    "🍣 works_draft から works への補完適用処理"
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT w.id, d.*
            FROM works w
            JOIN works_draft d ON w.id = d.work_id
            WHERE w.status = 'pending'
            """
        )
        rows = cur.fetchall()
        print(f"🧩 draft → works 補完対象: {len(rows)} 件")

        updated = 0

        for row in rows:
            work_id = row["work_id"]
            type_id = source_id = circle_id = author_id = None

            # type
            if row["type_raw"]:
                type_id = get_or_create_id(cur, "types", row["type_raw"])
            # source
            if row["source_raw"]:
                source_id = get_or_create_id(cur, "sources", row["source_raw"])
            # circle
            if row["circle_raw"]:
                circle_id = get_or_create_id(cur, "circles", row["circle_raw"])
            # author
            if row["author_raw"]:
                author_id = get_or_create_id(cur, "authors", row["author_raw"])

            # works 更新
            cur.execute(
                """
                UPDATE works
                SET type_id = ?, source_id = ?, circle_id = ?, author_id = ?, title = ?
                WHERE id = ?
                """,
                (
                    type_id,
                    source_id,
                    circle_id,
                    author_id,
                    row["title_raw"],
                    work_id,
                ),
            )

            # 完了状態登録
            cur.execute(
                """
                INSERT INTO work_completion_state (
                    work_id, circle_id_done, author_id_done, source_id_done, type_id_done
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(work_id) DO UPDATE SET
                    circle_id_done = excluded.circle_id_done,
                    author_id_done = excluded.author_id_done,
                    source_id_done = excluded.source_id_done,
                    type_id_done = excluded.type_id_done
                """,
                (
                    work_id,
                    int(circle_id is not None),
                    int(author_id is not None),
                    int(source_id is not None),
                    int(type_id is not None),
                ),
            )

            updated += 1

        conn.commit()
        print(f"✅ 補完完了: {updated} 件を更新しました")
