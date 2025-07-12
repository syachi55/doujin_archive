import os
import sys
import json
import csv
from datetime import datetime
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import folders.classifier as classifier


class FixedDatetime:
    @classmethod
    def now(cls):
        return datetime(2022, 1, 2, 3, 4)


def test_classify_and_export(tmp_path, monkeypatch):
    base = tmp_path / "base"
    base.mkdir()
    cat = base / "【画像10枚以上】"
    cat.mkdir()
    f1 = cat / "A"
    f1.mkdir()
    (f1 / "x.jpg").write_bytes(b"")
    (f1 / "other.txt").write_bytes(b"")
    f2 = cat / "B"
    f2.mkdir()
    (f2 / "y.png").write_bytes(b"")

    monkeypatch.setattr(classifier, "BASE_DIRS", [str(base)])
    monkeypatch.setattr(classifier, "CLASSIFY_OUTPUT_PREFIX", "pref")
    monkeypatch.setattr(classifier, "THRESHOLD", 5)
    monkeypatch.setattr(classifier, "datetime", FixedDatetime)

    classifier.classify_and_export()

    stem = "pref_thresh5_20220102-0304"
    json_path = base / f"{stem}.json"
    csv_path = base / f"{stem}.csv"
    assert json_path.is_file()
    assert csv_path.is_file()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(data) == 2
    names = sorted([rec["original_name"] for rec in data])
    assert names == ["A", "B"]

    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    csv_names = sorted(row["original_name"] for row in rows)
    assert csv_names == names
