from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dobble_library.deck_generator import render_deck


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render Dobble cards from a template JSON file."
    )
    parser.add_argument(
        "--templates",
        default=str(PROJECT_ROOT / "../Model_data/models/models_55_v2.json"),
        help="Path to the generated template JSON file.",
    )
    parser.add_argument(
        "--symbols-dir",
        default=str(PROJECT_ROOT / "../symbols"),
        help="Directory with source symbol images.",
    )
    parser.add_argument(
        "--output-dir",
        default="Model_data/output_cards",
        help="Directory for rendered card images.",
    )
    parser.add_argument(
        "--card-size-px", type=int, default=1134, help="Output card size in pixels."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1234,
        help="Random seed used to pick and shuffle cards.",
    )
    parser.add_argument(
        "--fit-scale",
        type=float,
        default=0.88,  # previous default 0.88
        help="Scale factor for symbols inside slots.",
    )
    parser.add_argument(
        "--rotation-sign",
        type=int,
        default=-1,
        choices=(-1, 1),
        help="Direction for slot rotation.",
    )
    parser.add_argument(
        "--circle-margin",
        type=float,
        default=0,  # previous 0.02
        help="Outside circle margin as fraction of card size (0-1).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    render_deck(
        json_path=args.templates,
        symbols_dir=args.symbols_dir,
        output_dir=args.output_dir,
        card_size_px=args.card_size_px,
        seed=args.seed,
        fit_scale=args.fit_scale,
        rotation_sign=args.rotation_sign,
        circle_margin=args.circle_margin,
    )


if __name__ == "__main__":
    main()
