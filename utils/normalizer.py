"🍣"

import unicodedata
import re

# 禁止記号 → 全角置換（Windows準拠）
FILENAME_REPLACEMENTS = {
    "/": "／",
    ":": "：",
    "?": "？",
    "*": "＊",
    "\\": "￥",
    '"': "”",
    "<": "＜",
    ">": "＞",
    "|": "｜",
}


def normalize_text(text: str) -> str:
    """
    一般的な正規化（Unicode正規化・空白処理）
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("　", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_for_matching(text: str) -> str:
    """
    照合キー用の厳密正規化（差異吸収を目的とする）
    - normalize_text を適用
    - 小文字化（case-folding）
    - 記号類はすべて削除（中黒・波ダッシュ含む）
    """
    text = normalize_text(text)
    text = text.lower()
    text = re.sub(r"[^\wぁ-んァ-ン一-龥]", "", text)
    return text


def normalize_for_filename(text: str) -> str:
    """
    ファイル・フォルダ名として安全な正規化
    - normalize_text を適用
    - 禁止記号を全角に置換
    """
    text = normalize_text(text)
    for k, v in FILENAME_REPLACEMENTS.items():
        text = text.replace(k, v)
    return text
