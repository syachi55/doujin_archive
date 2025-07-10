"🍣"

# io/classifier.py

import json
import csv
from pathlib import Path
from datetime import datetime

from config import BASE_DIRS, THRESHOLD, CLASSIFY_OUTPUT_PREFIX
from utils.image_counter import count_images


def classify_and_export():
    "🍣"
    for base_dir in BASE_DIRS:
        base = Path(base_dir)
        records = []

        # 1. 動的に分類フォルダ（【画像○枚以上】など）を検出
        for category_folder in base.iterdir():
            if not category_folder.is_dir():
                continue

            name = category_folder.name
            if not name.startswith("【画像") or "枚" not in name:
                continue  # 分類対象でない

            for folder in category_folder.iterdir():
                if not folder.is_dir():
                    continue

                image_count = count_images(folder)
                records.append(
                    {
                        "folder_path": str(folder.resolve()),
                        "original_name": folder.name,
                        "image_count": image_count,
                        "category": name,  # → 実在フォルダ名を記録
                    }
                )

        if not records:
            print(f"⚠️ {base.name} → 分類対象なし")
            continue

        # 2. ファイル名に THRESHOLD と日時を含めて識別可能に
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        threshold_label = f"thresh{THRESHOLD}"
        stem = f"{CLASSIFY_OUTPUT_PREFIX}_{threshold_label}_{timestamp}"

        json_path = base / f"{stem}.json"
        csv_path = base / f"{stem}.csv"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)

        print(f"✅ {base.name} → 分類結果を出力（{len(records)} 件）")
        print(f" - JSON: {json_path.name}")
        print(f" - CSV : {csv_path.name}")
