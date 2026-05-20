import json
import os
import tempfile

from json_template_generator.shortcuts import save_template_json
from json_template_generator.utils import Rectangle


def _make_rect() -> Rectangle:
    return Rectangle(x=0.5, y=0.5, w=0.1, h=0.1, ang_deg=0.0)


def test_save_template_json_writes_symbols_per_card():
    rect = _make_rect()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_template_json(
            [[rect]],
            circle_radius=0.47,
            symbols_per_card=6,
            output_file_path=path,
        )
        with open(path) as f:
            data = json.load(f)
        assert data["meta"]["symbols_per_card"] == 6
    finally:
        os.unlink(path)


def test_save_template_json_preserves_circle_meta():
    rect = _make_rect()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_template_json(
            [[rect]],
            circle_radius=0.47,
            symbols_per_card=8,
            output_file_path=path,
        )
        with open(path) as f:
            data = json.load(f)
        assert data["meta"]["circle_R"] == 0.47
        assert data["meta"]["circle_center"] == [0.5, 0.5]
    finally:
        os.unlink(path)
