import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analyze.analyzer import strip_prefix, try_match


def test_strip_prefix():
    assert strip_prefix("〔非表示〕[Circle] Title") == "[Circle] Title"
    assert strip_prefix("NoPrefix") == "NoPrefix"


def test_try_match_with_author():
    name = "｛CG集｝[サークル (作者)] タイトル (ソース)"
    result = try_match(name)
    assert result == {
        "type": "CG集",
        "circle": "サークル",
        "author": "作者",
        "title": "タイトル",
        "source": "ソース",
    }


def test_try_match_no_author():
    name = "｛漫画｝[サークル] タイトル (ジャンプ)"
    result = try_match(name)
    assert result == {
        "type": "漫画",
        "circle": "サークル",
        "title": "タイトル",
        "source": "ジャンプ",
    }


def test_try_match_circle_title():
    name = "[サークル] タイトル1"
    result = try_match(name)
    assert result == {
        "circle": "サークル",
        "title": "タイトル",
    }


def test_try_match_none():
    assert try_match("random text") == {"title": "random text"}
