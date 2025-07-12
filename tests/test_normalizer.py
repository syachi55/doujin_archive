import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.normalizer import normalize_for_filename

@pytest.mark.parametrize('original,expected', [
    ('hoge/fuga', 'hoge／fuga'),
    ('?:*', '？：＊'),
    ('abc', 'abc'),
])
def test_normalize_for_filename(original, expected):
    assert normalize_for_filename(original) == expected
