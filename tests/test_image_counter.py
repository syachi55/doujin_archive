import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.image_counter import count_images


def test_count_images(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.jpg").write_bytes(b"")
    (tmp_path / "b.txt").write_bytes(b"")
    (tmp_path / "sub" / "c.png").write_bytes(b"")
    assert count_images(tmp_path) == 2


def test_count_images_nonexistent(tmp_path):
    nonexistent = tmp_path / "nonexistent"
    assert count_images(nonexistent) == 0
