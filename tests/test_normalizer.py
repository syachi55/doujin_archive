import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.normalizer import (
    normalize_for_filename,
    normalize_text,
    normalize_for_matching,
)

@pytest.mark.parametrize('original,expected', [
    ('hoge/fuga', 'hoge／fuga'),
    ('?:*', '？：＊'),
    ('abc', 'abc'),
])
def test_normalize_for_filename(original, expected):
    assert normalize_for_filename(original) == expected


@pytest.mark.parametrize(
    'original,expected',
    [
        ('ＡＢＣ　ｄｅｆ', 'ABC def'),
        ('foo  bar\tbaz', 'foo bar baz'),
    ],
)
def test_normalize_text(original, expected):
    assert normalize_text(original) == expected


@pytest.mark.parametrize(
    'original,expected',
    [
        ('ＦｏｏーＢａｒ！', 'fooーbar'),
        (' ばなな★ ', 'ばなな'),
    ],
)
def test_normalize_for_matching(original, expected):
    assert normalize_for_matching(original) == expected
