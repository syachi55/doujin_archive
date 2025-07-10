"🍣"

# main.py

import argparse
from folders.rename import rename_all_confirmed_works
from analyze.analyzer import parse_original_names
from analyze.reviewer import apply_draft_to_works
from db.loader import load_classified_works
from sync.reconciler import compare_db_and_folders
from sync.cleaner import (
    delete_works_with_missing_folders,
    delete_physical_folders_not_in_db,
    delete_folders_with_zero_images,
    delete_orphan_relations,
)


def main():
    "🍣"
    parser = argparse.ArgumentParser(description="doujin_archive CLI")
    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # rename
    subparsers.add_parser("rename", help="confirmed 状態の作品をリネームしてログ出力")

    # analyze
    subparsers.add_parser("analyze", help="original_name を解析して works_draft に登録")

    # review
    subparsers.add_parser("review", help="works_draft から補完して works に反映")

    # load
    subparsers.add_parser("load", help="未登録フォルダを走査し、DBに初期登録")

    # sync
    subparsers.add_parser("sync", help="フォルダとDBの整合性チェック")

    # clean-db
    subparsers.add_parser(
        "clean-db", help="存在しない物理フォルダに対応する works レコードを削除"
    )

    # clean-fs
    subparsers.add_parser(
        "clean-fs", help="DBに登録されていない物理フォルダを削除（dry-run）"
    )

    # clean-zero
    subparsers.add_parser("clean-zero", help="画像0枚の物理フォルダを削除（dry-run）")

    # clean-orphan
    subparsers.add_parser("clean-orphan", help="孤立中間テーブルレコードの削除")

    args = parser.parse_args()

    if args.command == "rename":
        rename_all_confirmed_works()
    elif args.command == "analyze":
        parse_original_names()
    elif args.command == "review":
        apply_draft_to_works()
    elif args.command == "load":
        load_classified_works()
    elif args.command == "sync":
        compare_db_and_folders()
    elif args.command == "clean-db":
        delete_works_with_missing_folders()
    elif args.command == "clean-fs":
        delete_physical_folders_not_in_db(dry_run=True)  # 安全のため初回は dry-run
    elif args.command == "clean-zero":
        delete_folders_with_zero_images(dry_run=True)
    elif args.command == "clean-orphan":
        delete_orphan_relations()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
