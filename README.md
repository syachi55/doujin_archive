# doujin_archive

## 1. プロジェクト概要

このプロジェクトは、大量の同人作品フォルダを構造的に整理・管理するためのローカルアーカイブシステムである。
「1フォルダ＝1作品」を原則とし、検索性の向上と自己の嗜好分析を目的とする。

## 2. 基本構成

```bash
doujin_archive/
├─ main.py                # CLI操作エントリ
├─ config.py              # 対象パス、閾値などの定数定義
│
├─ db/                    # データベース操作群
│   ├─ schema.sql         # DDL（初期構造定義）
│   ├─ handler.py         # SELECT/INSERT/UPDATE 処理
│   ├─ loader.py          # フォルダからの初回登録
│   └─ migrator.py        # 構造変更スクリプト（任意）
│
├─ analyze/               # フォルダ名→構造情報抽出
│   ├─ patterns.py        # フォルダ名解析用の正規表現
│   ├─ analyzer.py        # original_name 解析→ works_draft 生成
│   └─ reviewer.py        # draft→確定データへの反映
│
├─ folders/               # フォルダ実体に関する処理
│   ├─ classifier.py      # 画像数による分類処理
│   ├─ rename.py          # フォルダ名の構造的リネーム
│   ├─ csv_exporter.py    # レビュー用CSV出力
│   └─ csv_importer.py    # 手動修正済みCSVの取り込み
│
├─ sync/                  # 実フォルダとDBの整合
│   ├─ reconciler.py      # 不整合の検出と登録・削除
│   └─ cleaner.py         # ゴミレコード・空フォルダ除去
│
├─ utils/                 # 汎用ユーティリティ
│   ├─ image_counter.py   # 画像数カウント
│   └─ normalizer.py      # 表記正規化（ファイル名用と照合用）
│
├─ data/                  # 実行時出力ファイル群
│   ├─ logs/              # 実行ログ
│   └─ exports/           # CSV/JSON出力
│
├─ README.md              # 本ファイル
└─ requirements.txt       # 依存パッケージ（現在は空）
```

## 3. 処理フロー概要（段階別）

+ 分類：画像枚数で粗く分類（CG集／同人誌など）→ `classifier.py`
+ 登録：分類済CSVを読み込み、DBに初回登録 → `loader.py`
+ 解析：original_name を構文解析し、中間構造に変換 → `analyzer.py`
+ レビュー：抽出結果を人力レビュー、CSV補正 → `csv_exporter.py`, `csv_importer.py`
+ 確定：`works_draft` を DB に反映し、 `status='confirmed'` → `reviewer.py`
+ リネーム：確定データに基づきフォルダ名を構造的にリネーム → `rename.py`
+ 整合：実フォルダとDBの存在確認、差分検出 → `reconciler.py`
+ 除去：0画像・破損・無効レコードなどをクリーン → `cleaner.py`

## 4. 設計原理（抜粋）

- 完全自己利用特化：他者提供前提の機能・表現は省略
- 構造記録・再現性重視：フォルダ名やDB構造は明確な規則で一貫管理
- 責務分離：解析・分類・補完・同期などは明確に分離されたモジュール構成
- メタ情報の確実な補完：作者・サークル・出典等を正規化・辞書管理

## 5. 今後の展開予定（構想）

- `viewer/`：検索・閲覧GUI（例：streamlit）

## 6. 動作環境

- Python 3.13.3
- 現時点では 標準ライブラリのみで動作
- 仮想環境推奨（但し必須ではない）

```bash
python -m venv venv
venv\Scripts\activate
```

## 7. 備考

- このREADMEは ChatGPT との設計共有・進行管理のために整備された。
- codex による分担作業・履歴の可視化を前提とした構造整理が進行中。
## 8. テスト実行方法

```bash
pip install -r requirements.txt
pytest
```

