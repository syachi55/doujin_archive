"🍣"

# config.py

from pathlib import Path

# DB
DB_PATH = Path("metadata.sqlite3")

# 対象フォルダ群（BASE_DIRS）
BASE_DIRS = [
    r"E:\2021年12月19日ダウンロード",
    r"E:\2023年05月",
    r"E:\2023年06月",
    r"E:\2023年07月",
    r"E:\2023年08月",
    r"E:\2023年09月",
    r"E:\2023年10月",
    r"E:\2023年11月",
    r"E:\2023年12月",
    r"E:\2024年01月",
    r"E:\2024年02月",
    r"E:\2024年03月",
    r"E:\2024年04月",
    r"E:\2024年05月",
    r"E:\2024年06月",
    r"E:\2024年07月",
    r"E:\2024年08月",
    r"E:\2024年09月",
    r"E:\2024年10月",
    r"E:\2024年11月",
    r"E:\2024年12月",
    r"E:\2025年01月",
    r"E:\2025年02月",
    r"E:\2025年03月",
    r"E:\2025年04月",
    r"E:\2025年05月",
    r"E:\2025年06月",
    r"E:\Cons_Game_01同人CG集",
    r"E:\Cons_Movie_01同人誌",
    r"E:\Cons_Movie_02同人CG集",
    r"E:\Cons_Movie_02同人誌",
    r"E:\Cons_Movie_02同人誌2",
    r"E:\Cons_Movie_02同人誌3",
    r"E:\Cons_Movie_02同人誌4",
    r"E:\Pro_Movie_01商業誌",
    r"E:\Pro_Movie_01同人CG集",
    r"E:\一時退避ダウンロード2",
    r"E:\一時退避ダウンロード4",
    r"E:\一時避難WEB漫画",
    r"E:\一時避難ダウンロード",
    r"E:\一時避難ダウンロード3",
    r"E:\一時避難ダウンロード5",
    r"E:\一時避難商業誌",
    r"E:\一時避難同人CG集",
    r"E:\一時避難同人誌",
]

# 画像枚数による分類閾値
THRESHOLD = 100

# 出力ファイル共通接頭辞
CLASSIFY_OUTPUT_PREFIX = "classification_result"
