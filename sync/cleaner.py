"🍣"

# sync/cleaner.py

import shutil
from pathlib import Path
from db.handler import get_connection
from config import BASE_DIRS
from utils.image_counter import count_images


def delete_works_with_missing_folders():
    """
    実体が存在しない works レコードを削除（DBのみ）
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, folder_path FROM works")
        rows = cur.fetchall()

        targets = []
        for row in rows:
            folder = Path(row["folder_path"])
            if not folder.exists():
                targets.append(row["id"])

        print(f"❌ 実体のない works 削除対象: {len(targets)} 件")

        for wid in targets:
            cur.execute("DELETE FROM works WHERE id = ?", (wid,))
        conn.commit()

        print(f"✅ 削除完了: {len(targets)} 件")


def get_all_db_folder_paths() -> set[str]:
    "DBに登録された folder_path を正規化して返す"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT folder_path FROM works")
        return {str(Path(row["folder_path"]).resolve()) for row in cur.fetchall()}


def delete_physical_folders_not_in_db(dry_run: bool = True):
    """
    DBに登録されていない物理フォルダを削除（安全のため dry_run=True がデフォルト）
    """
    registered_paths = get_all_db_folder_paths()
    deleted_count = 0
    skipped_count = 0

    for base in BASE_DIRS:
        base_path = Path(base)
        if not base_path.exists():
            continue

        for folder in base_path.iterdir():
            if not folder.is_dir():
                continue

            full_path = str(folder.resolve())
            if full_path not in registered_paths:
                print(f"[unregistered] {full_path}")
                if dry_run:
                    skipped_count += 1
                else:
                    try:
                        shutil.rmtree(folder)
                        print(f"🗑️ deleted: {full_path}")
                        deleted_count += 1
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        print(f"[error] {e}")
            else:
                skipped_count += 1

    if dry_run:
        print(
            f"🔎 Dry-run: 削除候補 {deleted_count + skipped_count - len(registered_paths)} 件（実行なし）"
        )
    else:
        print(f"✅ 削除完了: {deleted_count} 件 / 無視: {skipped_count} 件")


def delete_folders_with_zero_images(dry_run: bool = True):
    """
    画像ファイルが1枚も含まれていないフォルダを削除（再帰走査）
    config.BASE_DIRS 配下の直下フォルダが対象
    """

    deleted = 0
    skipped = 0

    for base in BASE_DIRS:
        base_path = Path(base)
        if not base_path.exists():
            continue

        for folder in base_path.iterdir():
            if not folder.is_dir():
                continue

            count = count_images(folder)
            if count == 0:
                print(f"[zero] {folder}")
                if dry_run:
                    skipped += 1
                else:
                    try:
                        shutil.rmtree(folder)
                        print(f"🗑️ deleted: {folder}")
                        deleted += 1
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        print(f"[error] {e}")
            else:
                skipped += 1

    if dry_run:
        print(f"🔎 Dry-run: 画像0枚フォルダ候補 {deleted + skipped} 件（実行なし）")
    else:
        print(f"✅ 削除完了: {deleted} 件 / 無視: {skipped} 件")


def delete_orphan_relations():
    """
    works に対応するレコードが存在しない中間テーブルの孤立レコードを削除
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # 孤立 work_circle_authors
        cur.execute(
            """
            DELETE FROM work_circle_authors
            WHERE work_id NOT IN (SELECT id FROM works)
        """
        )
        deleted_authors = cur.rowcount

        # 孤立 work_sources
        cur.execute(
            """
            DELETE FROM work_sources
            WHERE work_id NOT IN (SELECT id FROM works)
        """
        )
        deleted_sources = cur.rowcount

        # 孤立 work_completion_state
        cur.execute(
            """
            DELETE FROM work_completion_state
            WHERE work_id NOT IN (SELECT id FROM works)
        """
        )
        deleted_states = cur.rowcount

        conn.commit()

    print("✅ 孤立レコード削除完了")
    print(f" - work_circle_authors: {deleted_authors} 件")
    print(f" - work_sources: {deleted_sources} 件")
    print(f" - work_completion_state: {deleted_states} 件")
