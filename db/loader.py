"🍣"

# db/loader.py

import json
import re
from pathlib import Path
from db.handler import insert_work, work_exists
from config import BASE_DIRS, CLASSIFY_OUTPUT_PREFIX


# 🔍 一番新しい JSON ファイルを探す
def find_latest_json(base_dir: Path) -> Path | None:
    "🍣"
    pattern = re.compile(rf"{CLASSIFY_OUTPUT_PREFIX}_.*\.json")
    json_files = [f for f in base_dir.glob("*.json") if pattern.match(f.name)]
    if not json_files:
        return None
    return max(json_files, key=lambda f: f.stat().st_mtime)


def load_classified_works():
    "🍣"
    total = 0
    skipped = 0

    for base_dir in BASE_DIRS:
        base = Path(base_dir)
        json_path = find_latest_json(base)

        if not json_path:
            print(f"⚠️ 分類結果が見つかりません: {base}")
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        print(f"📤 {json_path.name} をロード中...")

        for record in records:
            folder = record["folder_path"]
            name = record["original_name"]
            count = record["image_count"]

            if work_exists(folder):
                skipped += 1
                continue

            insert_work(folder, name, count)
            total += 1

        print(f"📥 {base.name} → 新規登録: {total} 件（スキップ: {skipped}）")
