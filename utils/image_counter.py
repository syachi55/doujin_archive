"🍣"

# utils/image_counter.py

import os
from pathlib import Path

# 判定対象の画像拡張子（小文字）
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def count_images(folder_path: Path | str) -> int:
    """
    指定フォルダ以下の画像ファイル数を再帰的にカウントする。
    """
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        return 0

    count = 0
    for _root, _, files in os.walk(folder):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in IMAGE_EXTENSIONS:
                count += 1
    return count
