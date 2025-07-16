"🍣"

# folders/scanner.py

import json
from datetime import datetime
from pathlib import Path

from db.handler import get_connection
from utils.image_counter import count_images


def scan_and_export():
    """Scan active base directories and export folder info as JSON."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT path FROM scan_targets WHERE active = 1"
        ).fetchall()

    for row in rows:
        base = Path(row["path"])
        if not base.exists():
            print(f"[warn] base directory not found: {base}")
            continue

        records = []
        for child in base.iterdir():
            if not child.is_dir():
                continue
            records.append(
                {
                    "folder_path": str(child.resolve()),
                    "original_name": child.name,
                    "image_count": count_images(child),
                    "status": "pending",
                }
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        json_path = base / f"scan_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        print(f"✅ {base.name} → スキャン結果を出力（{len(records)} 件）")
        print(f" - JSON: {json_path.name}")
