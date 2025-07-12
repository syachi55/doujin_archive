"🍣"

# analyze/analyzer.py

import re
from analyze.patterns import PATTERN_SEQUENCE
from db.handler import get_connection


# プレフィックス除去（例：〔非表示〕）
def strip_prefix(name: str) -> str:
    "🍣"
    return re.sub(r"^〔.+?〕", "", name)


def strip_suffix_id(name: str) -> str:
    "suffix '#id123' を除去する"
    return re.sub(r"\s*#id\d+$", "", name)


# 最初にマッチしたパターンを適用
def try_match(name: str) -> dict | None:
    "🍣"
    for pattern in PATTERN_SEQUENCE:
        match = pattern.match(name)
        if match:
            return match.groupdict()
    return None


# works → works_draft を生成・更新
def parse_original_names():
    "🍣"
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("SELECT id, original_name FROM works WHERE status = 'pending'")
        rows = cur.fetchall()

        print(f"🔍 解析対象: {len(rows)} 件")

        inserted = 0

        for row in rows:
            work_id = row["id"]
            name = strip_prefix(row["original_name"])
            name = strip_suffix_id(name)

            parsed = try_match(name)
            if not parsed:
                continue

            cur.execute(
                """
                INSERT INTO works_draft (
                    work_id, circle_raw, author_raw, source_raw, type_raw, title_raw
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(work_id) DO UPDATE SET
                    circle_raw = excluded.circle_raw,
                    author_raw = excluded.author_raw,
                    source_raw = excluded.source_raw,
                    type_raw = excluded.type_raw,
                    title_raw = excluded.title_raw
            """,
                (
                    work_id,
                    parsed.get("circle"),
                    parsed.get("author"),
                    parsed.get("source"),
                    parsed.get("type"),
                    parsed.get("title"),
                ),
            )

            inserted += 1

        conn.commit()
        print(f"✅ 構文解析完了: {inserted} 件の draft を登録")
