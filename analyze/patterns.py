"🍣"

# analyze/patterns.py

import re

# 【タイプ】[サークル名 (作者名)] タイトル (ソース) [_1]
PATTERN_WITH_AUTHOR = re.compile(
    r"^｛(?P<type>.+?)｝\[(?P<circle>.+?) \((?P<author>.+?)\)\] (?P<title>.+?) \((?P<source>.*?)\)(?:[_\s]?\d+)?$"
)

# 【タイプ】[サークル名] タイトル (ソース) [_1]
PATTERN_NO_AUTHOR = re.compile(
    r"^｛(?P<type>.+?)｝\[(?P<circle>.*?)\] (?P<title>.+?) \((?P<source>.*?)\)(?:[_\s]?\d+)?$"
)

# [サークル名] タイトル [_1]
PATTERN_CIRCLE_TITLE = re.compile(r"^\[(?P<circle>.+?)\] (?P<title>.+?)(?:[_\s]?\d+)?$")

# タイトル (ソース) [_1]
PATTERN_TITLE_SOURCE = re.compile(r"^(?P<title>.+?) \((?P<source>.+?)\)(?:[_\s]?\d+)?$")

# タイトルのみ
PATTERN_TITLE_ONLY = re.compile(r"^(?P<title>.+?)(?:[_\s]?\d+)?$")

# 正規表現リスト（上から順に適用）
PATTERN_SEQUENCE = [
    PATTERN_WITH_AUTHOR,
    PATTERN_NO_AUTHOR,
    PATTERN_CIRCLE_TITLE,
    PATTERN_TITLE_SOURCE,
    PATTERN_TITLE_ONLY,
]
