"🍣"

# sync/reconciler.py

from pathlib import Path
from db.handler import get_connection
from config import BASE_DIRS


def get_all_db_paths() -> dict:
    """
    DBに登録されている folder_path → (id, original_name) のマッピング
    パスは絶対パス（Path.resolve()）で正規化
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, folder_path, original_name FROM works")
        return {
            str(Path(row["folder_path"]).resolve()): (row["id"], row["original_name"])
            for row in cur.fetchall()
        }


def get_all_physical_folders() -> list[Path]:
    """
    config.BASE_DIRS に登録されたフォルダ以下の直下フォルダ（作品フォルダ）を収集
    """
    all_folders = []
    for base in BASE_DIRS:
        base_path = Path(base)
        if not base_path.exists():
            print(f"[warn] base directory not found: {base}")
            continue
        for child in base_path.iterdir():
            if child.is_dir():
                all_folders.append(child.resolve())
    return all_folders


def compare_db_and_folders():
    """
    DB と 物理フォルダの整合性を比較し、差分を出力する
    - DBにあるが物理にない（消失 or 移動）
    - 物理にあるがDBにない（未登録）
    """
    db_paths = get_all_db_paths()
    physical_paths = get_all_physical_folders()

    db_set = set(db_paths.keys())
    fs_set = set(str(p) for p in physical_paths)

    missing_on_fs = db_set - fs_set
    missing_on_db = fs_set - db_set

    print("🧩 整合性チェック結果")
    print(f"📁 DB登録：{len(db_set)} 件")
    print(f"📂 実フォルダ：{len(fs_set)} 件")
    print(f"❌ 実体が存在しない（DBにだけある）：{len(missing_on_fs)} 件")
    print(f"➕ 未登録（物理にだけある）：{len(missing_on_db)} 件")

    if missing_on_fs:
        print("\n[DBにあって物理にないフォルダ一覧]")
        for path in sorted(missing_on_fs):
            _work_id, original = db_paths[path]
            print(f"- {path}  ← original_name: {original}")

    if missing_on_db:
        print("\n[物理にあってDBにないフォルダ一覧]")
        for path in sorted(missing_on_db):
            print(f"- {path}")
